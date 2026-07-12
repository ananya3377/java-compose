Common Issues and Solutions 

1. Oracle Solution failing locally.
  
Meaning : solve.sh is not able to pass all of the tests mentioned in test_outputs.py

Solution : you can direct the agent to first implement the solve.sh , and generate the tests according to the implementation of solve.sh, or (use Cursor it fixes this automatically)

2. Tmux issue 

Meaning : Usually for tmux issues, memory limit gets exceeded 

Solution : Increase the memory limit 

3. Build timeout (7200 s) on the platform :

Meaning : has some dockerfile issues

Solution : Cursor fixes this itself, (increase build_timeout to 1800)

4. Oracle Solution failed on platform but passes locally.

Solution : See oraclefailonplatform.md

5. Task Instruction Sufficiency Failure : 

	Case 1 : few runs claim that specs are ambiguous or has spec issues 
	Case 2 : Major runs claim that it has spec issues 

Solution : 
	Case 1 : ignore 
	Case 2 : Fix that you might find the exact actions (bottom of the generated summary as Recommended)

6. Empty Summary on Platform : 

Solution : 

An empty summary from the LLMaJ review typically means the agents couldn't start their session - most commonly because tmux and/or asciinema are missing from your Dockerfile.

The agent runtime requires both tmux and asciinema to be installed. Without them, agents cannot run at all, which results in no verifier output and an empty/"NOT_APPLICABLE" summary.

Fix: Add both to your environment/Dockerfile:

dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends tmux asciinema \
    && rm -rf /var/lib/apt/lists/*

7. Blank Agent Review

Solution : 
This is a known platform issue right now and they are working on it, the best thing to do is tweak the task in an inconsequential way (changing a letter, period, space, etc) and try resubmitting and doing agent checks again.

Note : Most of the issues are solved by the rules in workdir zip file itself , if new issues will come that will be updated here.


IMP:-If the task is medium, make sure you fix the task.toml difficulty field to medium, rezip it and then submit.

Make sure to take care of Rubric