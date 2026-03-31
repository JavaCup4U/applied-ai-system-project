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
I used AI tools for asisstance with the designing and refactoring of issues I found as an issue with the app. Putting myself in the shoes of the user and trying to make an actual schedule and realizing what flaws the design I had initially thougt of had and used AI as a collaborator to assist with making the experience better for the user.
- What kinds of prompts or questions were most helpful?
The most helpful prompts were the ones that felt almost natural to ask after eperiencing the app as a user and asking how to make it better. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
One moment I did not accpet an AI suggestion as is is where it it deciced on its own to start adding more features that were not in my original design and I felt were not necessary.
- How did you evaluate or verify what the AI suggested?
I looked over and read what it was suggesting and though about how it would affect the application on its own and whehter it woult actually be a good feature or expeerience for the user of the app.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
I tested the task creation and retrieval behaviors.
I also tested the filtering and sorting of tasks by the users preferences and constraints. 
I tested the scenario where the owner owns multiple pets and how each task would be assigned to the correct pet.
- Why were these tests important?
They are important because they are the core behaviors of the app and if they don't work then the app doesn't funtion properly and could cause confustion for a user. 

**b. Confidence**

- How confident are you that your scheduler works correctly?
I am confident it works correctly but there are still kinks that need to be worked out and edge cases that were probably missed. 
- What edge cases would you test next if you had more time?
I would test the cases where there are multiple tasks being saved and the front end shows them but the back end is not saving after the edits or tasks are removed with the removal button. 
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I am satisfied with the overall core functionality of the app and how it allows users to create a task and assign it to a pet. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would improve the Schedule generation for sure. It has some issues that need to be worked out and I would like it to be more accurate about the tasks and what it generates after a task is edited or removed. 
**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
I learned that it takes a lot more than just zooming in on one specific area and that you have to consider a much larger picture when creating something even like a schedule generator. There is a lot of different factors to consider at every step. AI can be a great and helpful tool but it is not going to get everything right and as the designer/ engineer it is up to you to make the final decision on the process and testing to verify that it is the right way to go. 