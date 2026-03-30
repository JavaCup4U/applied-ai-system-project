# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design. 
Every user should have a class that stores their information and pet information and preferences.
There should be a class for the schedule/ plan and any extra priorities or constraints that the owner would have as a preference for the schedule.
The plan class should be responsible for generating the plan based on the users preferences and the constraints and priorities given by the user. 
- What classes did you include, and what responsibilities did you assign to each?
The classes I included are the user class, which is responsible for storing the users information and pet information and preferences. 
The schedule class, which is responsible for creating and managing the schedule. 
The constraints class, which is responsible for storing any constraints or priorities that the user has for the schedule. 
The plan class, which is responsible for generating the plan based on the users preferences and the constraints and priorities given by the user. 


**b. Design changes**

- Did your design change during implementation? 
Yes it did. 

- If yes, describe at least one change and why you made it.
I made some changes to the way the database was loading in the app co pilot mentioned how loading the entire list for tasks and pets was inefficient and suggested loading by implementing lazy loading. So now the app will ask for the next couple of tasks or pets instead of loading the entire list at once.
I also changed the orginzation for the the database which co pilot suggested because before it could have a bunch of pets and tasks but we wouldn't know which tasks were for which pets or user. Now they each have their own user ID and pet ID attached so the app knows exactly who owns what and prevents lost data. 
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
One trade off is that it is fast and predictable but not globally optimal. It is fast because of the greedy algorithm that is used to generate a schedule. It is not optimal because it does not consider all possible cominations of tasks. 
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
