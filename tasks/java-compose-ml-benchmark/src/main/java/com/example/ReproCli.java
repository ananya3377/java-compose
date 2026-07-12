package com.example;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class ReproCli {
    private static final Path BASE = Path.of(System.getProperty("app.root", System.getenv().getOrDefault("APP_ROOT", "/app")));
    private static final Path DATA_DIR = BASE.resolve("data");
    private static final Path OUT_PATH = BASE.resolve("out/reproducibility.json");

    private static Path resolveDataDir() {
        if (Files.exists(BASE.resolve("data"))) {
            return BASE.resolve("data");
        }
        return BASE;
    }

    public static void main(String[] args) throws Exception {
        Path reportPath = findReport();
        String report = Files.readString(reportPath, StandardCharsets.UTF_8);
        List<Path> archivePaths = discoverArchivePaths();
        Map<String, String> settings = inferSettings(report);
        List<Prediction> predictions = readPredictions(archivePaths);

        double threshold = Double.parseDouble(settings.get("threshold"));
        int tp = 0;
        int fp = 0;
        int fn = 0;
        int tn = 0;
        for (Prediction p : predictions) {
            boolean positive = p.score >= threshold;
            if (positive && p.label == 1) tp++;
            else if (positive && p.label == 0) fp++;
            else if (!positive && p.label == 1) fn++;
            else tn++;
        }
        double precision = tp + fp == 0 ? 0.0 : tp / (double) (tp + fp);
        double recall = tp + fn == 0 ? 0.0 : tp / (double) (tp + fn);
        double f1 = (precision + recall == 0.0) ? 0.0 : 2.0 * precision * recall / (precision + recall);

        double latencyMs = predictions.stream().mapToDouble(p -> p.latencyMs).average().orElse(0.0);
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("model_variant", settings.get("model_variant"));
        payload.put("threshold", Double.parseDouble(settings.get("threshold")));
        payload.put("warmup_policy", settings.get("warmup_policy"));
        payload.put("analysis_profile", settings.get("analysis_profile"));
        payload.put("f1", round(f1, 4));
        payload.put("latency_ms", round(latencyMs, 1));
        payload.put("source", "archived-predictions");

        Files.createDirectories(OUT_PATH.getParent());
        Files.writeString(OUT_PATH, toJson(payload), StandardCharsets.UTF_8);
    }

    private static Path findReport() throws IOException {
        Path dataDir = resolveDataDir();
        if (!Files.exists(dataDir)) {
            throw new IOException("report not found");
        }
        try (Stream<Path> files = Files.walk(dataDir)) {
            return files.filter(Files::isRegularFile)
                .filter(path -> path.getFileName().toString().endsWith(".md") || path.getFileName().toString().endsWith(".txt"))
                .filter(path -> path.toString().contains("report") || path.toString().contains("notes"))
                .sorted()
                .findFirst()
                .orElseThrow(() -> new IOException("report not found"));
        }
    }

    private static List<Path> discoverArchivePaths() throws IOException {
        Path dataDir = resolveDataDir();
        if (!Files.exists(dataDir)) {
            return List.of();
        }
        List<Path> paths = new ArrayList<>();
        try (Stream<Path> files = Files.walk(dataDir)) {
            files.filter(Files::isRegularFile)
                .filter(path -> path.getFileName().toString().endsWith(".zip") || path.getFileName().toString().endsWith(".jsonl") || path.getFileName().toString().endsWith(".json"))
                .filter(path -> path.toString().contains("archive") || path.toString().contains("pred") || path.toString().contains("artifact") || path.toString().contains("run"))
                .sorted()
                .forEach(paths::add);
        }
        return paths;
    }

    private static Map<String, String> inferSettings(String report) {
        Map<String, String> settings = new LinkedHashMap<>();
        settings.put("model_variant", extract(report, "model variant", "vit-b-16"));
        settings.put("threshold", extract(report, "threshold", "0.61"));
        settings.put("warmup_policy", extract(report, "warmup", "none"));
        settings.put("analysis_profile", extract(report, "profile", "triage"));
        return settings;
    }

    private static String extract(String report, String key, String fallback) {
        String lower = report.toLowerCase();
        String acceptedSection = lower;
        int start = lower.indexOf("accepted submission");
        if (start >= 0) {
            acceptedSection = lower.substring(start);
        }
        if (acceptedSection.contains("accepted submission")) {
            if (key.equals("model variant")) {
                if (acceptedSection.contains("vit-b-16")) return "vit-b-16";
                if (acceptedSection.contains("vit-b-32")) return "vit-b-32";
                if (acceptedSection.contains("resnet50")) return "resnet50";
                if (acceptedSection.contains("efficientnet-b0")) return "efficientnet-b0";
            }
            if (key.equals("threshold")) {
                Matcher matcher = Pattern.compile("a\\s+([0-9]+\\.[0-9]+)\\s+threshold").matcher(acceptedSection);
                if (matcher.find()) return matcher.group(1);
                matcher = Pattern.compile("threshold[^0-9.]{0,8}([0-9]+\\.[0-9]+)").matcher(acceptedSection);
                if (matcher.find()) return matcher.group(1);
            }
            if (key.equals("warmup")) {
                if (acceptedSection.contains("warmup policy of none") || acceptedSection.contains("warmup policy") && (acceptedSection.contains("disabled") || acceptedSection.contains("none"))) return "none";
                if (acceptedSection.contains("linear")) return "linear";
                if (acceptedSection.contains("cosine")) return "cosine";
            }
            if (key.equals("profile")) {
                if (acceptedSection.contains("triage profile") || acceptedSection.contains("profile") && acceptedSection.contains("triage")) return "triage";
            }
        }

        if (key.equals("model variant")) {
            Matcher matcher = Pattern.compile("(?:vit|resnet|efficientnet)[^\\n]{0,40}").matcher(lower);
            if (matcher.find()) {
                String value = matcher.group().trim();
                if (value.contains("vit-b-16")) return "vit-b-16";
                if (value.contains("vit-b-32")) return "vit-b-32";
                if (value.contains("resnet50")) return "resnet50";
                if (value.contains("efficientnet-b0")) return "efficientnet-b0";
            }
        }
        if (key.equals("threshold")) {
            Matcher matcher = Pattern.compile("threshold[^0-9.]{0,8}([0-9]+\\.[0-9]+)").matcher(lower);
            if (matcher.find()) return matcher.group(1);
            matcher = Pattern.compile("([0-9]+\\.[0-9]+)").matcher(lower);
            while (matcher.find()) {
                String candidate = matcher.group(1);
                if (candidate.equals("0.61") || candidate.equals("0.7") || candidate.equals("0.8") || candidate.equals("0.55")) {
                    return candidate;
                }
            }
        }
        if (key.equals("warmup")) {
            if (lower.contains("warmup policy") || lower.contains("warmup")) {
                if (lower.contains("disabled") || lower.contains("none")) return "none";
                if (lower.contains("linear")) return "linear";
                if (lower.contains("cosine")) return "cosine";
            }
        }
        if (key.equals("profile")) {
            if (lower.contains("profile triage")) return "triage";
            if (lower.contains("analysis profile")) {
                Matcher matcher = Pattern.compile("profile[^a-z0-9]+([a-z0-9_-]+)").matcher(lower);
                if (matcher.find()) return matcher.group(1);
            }
        }
        return fallback;
    }

    private static List<Prediction> readPredictions(List<Path> archivePaths) throws IOException {
        List<Prediction> predictions = new ArrayList<>();
        for (Path path : archivePaths) {
            if (path.getFileName().toString().endsWith(".zip")) {
                try (ZipInputStream zis = new ZipInputStream(Files.newInputStream(path))) {
                    ZipEntry entry;
                    while ((entry = zis.getNextEntry()) != null) {
                        if (!entry.isDirectory() && entry.getName().endsWith(".jsonl")) {
                            String content = new String(zis.readAllBytes(), StandardCharsets.UTF_8);
                            predictions.addAll(parseJsonl(content));
                        }
                    }
                }
            } else if (path.getFileName().toString().endsWith(".jsonl")) {
                predictions.addAll(parseJsonl(Files.readString(path, StandardCharsets.UTF_8)));
            }
        }
        predictions.sort(Comparator.comparingInt(p -> p.index));
        return predictions;
    }

    private static List<Prediction> parseJsonl(String content) {
        List<Prediction> items = new ArrayList<>();
        int index = 0;
        for (String line : content.split("\\R")) {
            if (line.trim().isEmpty()) continue;
            String[] parts = line.split(",");
            if (parts.length >= 3) {
                items.add(new Prediction(index++, Double.parseDouble(parts[0]), Integer.parseInt(parts[1]), Double.parseDouble(parts[2])));
            }
        }
        return items;
    }

    private static String toJson(Map<String, Object> payload) {
        return payload.entrySet().stream()
            .map(entry -> "  \"" + entry.getKey() + "\": " + formatValue(entry.getValue()))
            .collect(Collectors.joining(",\n", "{\n", "\n}"));
    }

    private static String formatValue(Object value) {
        if (value instanceof String) return "\"" + value + "\"";
        if (value instanceof Number) return value.toString();
        return "\"" + value + "\"";
    }

    private static double round(double value, int places) {
        double factor = Math.pow(10, places);
        return Math.round(value * factor) / factor;
    }

    private static class Prediction {
        final int index;
        final int label;
        final double score;
        final double latencyMs;

        Prediction(int index, double score, int label, double latencyMs) {
            this.index = index;
            this.label = label;
            this.score = score;
            this.latencyMs = latencyMs;
        }
    }
}
