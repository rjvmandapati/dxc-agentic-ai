# Lab 7 answers

Saved 2026-10-12 10:32 · model: AWS Bedrock

**Q1. In tab 2, how many tokens did compaction save (%), and did AskIT still know your employee id at the end?**

it saved 5102 tokens when the compaction is turned-on.  No, AskIT did not know when we turned on compaction

**Q2. A client's helpdesk chats run 40+ turns. Would you switch compaction on? At what size, and what is the risk?**

yes defintely, because there will be more tokens sent as the number of turns is more. I will turn on compaction as 4 to bundle every 4 chats. Risk is the cost.

**Q3. Name one fact that SHOULD go to long-term memory and one that should NOT. Why?**

non-personal data should not go. any other contextual content like system id, name should go.
