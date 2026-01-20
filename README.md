# narr0w
 
Our project, **narr0w**, helps teams narrow their open tickets down to zero.
 
* * *
 
## Part 0: The Problem (Personal Experience)
 
Everyone on our team works in IT.
 
We’ve worked as:
 
- Network Technicians
- DevOps Engineers
- Cybersecurity SOC Analysts
- IT Help Specialists

No matter the role, we all start our day the same way — by opening a ticket queue that’s already full.
 
Before we can actually *solve* problems, we have to do something else first: **triage**.
 
Triage means deciding:

- What the ticket actually is
- How urgent it is
- And who is best equipped to handle it

That decision isn’t simple. You have to consider someone’s skill set, their current workload, and the type of issue.
 
And here’s the real problem:
 
**That ticket was probably triaged already.**
 
Before it ever reached us, a manager had to decide which team it belonged to. Then another person might re-triage it before it finally lands in the queue.
 
So the same ticket gets evaluated multiple times by multiple people, before any real work even begins.
 
* * *
 
## Part 1: Autonomous Triage
 
That’s where **narr0w** comes in.
 
We built a system that uses AI to **autonomously triage incoming tasks**.
 
narr0w evaluates:

- The content of the ticket
- Each person’s skills
- Each person’s current workload

And then assigns the ticket to the **best possible person at the best possible time**.
 
The goal is fairness and efficiency.
 
We also include a **confidence score**, which shows how confident the AI is in its triage decision.  
 This allows humans to quickly review low-confidence cases while high-confidence tickets move forward automatically.
 
* * *
 
## Part 2: Learning AI Agents
 
When narr0w is first deployed, a manager provides a brief explanation of how tickets *should* be triaged.
 
From there, the system learns from:

- Past triage decisions
- Historical tickets
- Company documentation

Over time, narr0w becomes better at making decisions that match how **your organization** actually works — not some generic workflow.
 
Based on time savings alone, we estimate narr0w can save large organizations **over $50,000 per year**, simply by eliminating repeated manual triage across multiple teams.
 
* * *
 
## How This Helps Developers
 
For developers, this is a massive improvement.
 
Instead of:

- Constant interruptions
- Poorly written or misrouted tickets
- Tasks bouncing between teams

Developers receive:

- Well-classified issues
- Accurate priority levels
- Clear AI reasoning explaining *why* the task was assigned to them

This means developers spend more time building, and less time sorting.
 
* * *
 
## Part 3: **Code-Mode**: AI That Acts
 
When a ticket is tagged as a coding task, narr0w can trigger **Code-Mode**
 
**Code-Mode** is a custom AI Agent that is given the context of your current repository, and creates commits and pull requests to perform an assigned task. 
 
During its runtime it will:

- Analyze the repository
- Break the task into actionable steps
- Create GitHub issues
- Create branches
- Submit pull requests

All automatically.
 
In the demo, we show:

1. A ticket submitted from an external source
2. narr0w triaging it in real time
3. AI agents spinning up while we explain the system
4. A pull request appearing in GitHub for human review

## **Code-Mode**
**Code-Mode** is more than a suggestion tool, it allows you to rapidly prototype from anywhere, developing at the speed that you can send a text.
 
narr0w removes friction before work even starts.
 
By eliminating repetitive triage, routing work intelligently, and empowering AI agents to act, teams can finally focus on what matters most:
 
**Solving problems, not sorting them.**
