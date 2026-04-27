







# PawPal+ (Module 2 Project) 
Original Goals and Capabilities:
- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

# Demo Video



https://github.com/user-attachments/assets/20b3c380-3010-4e7f-b3a0-ab0925d9481c.mp4









# Title and Summary
The pawpal+ applied system is designed to assist pet owners in managing and creating schedules for their tasks. The system includes an agent that the user is able to chat with . The agent can obtain information from a knowledge base that contains pet care information based on the breed. 
Pet information is an important part about being an owner and vital to the care of thier companion. Being informed about their needs is an important part of a pets lifesyle. The system is designed to be user friendly and provide an easy way for pet owners to easily manage their pets care and tasks. 


# Archicture Overview
The system starts with the user input, then the User Interface sends the users input to the agent . Before the agent recieves the users input, it is checked by the Input Validator which filters out any unsafe or malformed input. 
Then once the input is sanitized, the agent is able to proccess the input and decides what tools to use in order to answer the users input. 
It goes to the Knowledge Base wheich is able to request information from the retriever from the current knowledge base about information about the pet and the specific breed they might have mentioned. 
Everything is logged to show what actions the agent took which is more transperent and allows users to know how the agent came to its conclusion. 
The result is then able to be reviewed by the user and if something is off they can make manual changes which is like a human in the loop check. 

# Setup Insutructions 
To set up the system, you will need to follow these steps:
1. Clone the repository to your local machine.
2. Create a virtual environment and activate it.
3. Install the required dependencies using pip.
4. Run the Streamlit app using the command `streamlit run app.py`.
5. Follow the prompts in the app to enter your pet information and generate a schedule. 

# Sample Interactions 
1st sample interaction: 
User asking about how often their dog should be fed.
The agent searches the knowledge base in this case the base it searches is the 'dogs.txt' file and finds the relevaant information at the "DOG CARE GUIDE FEEDING" section and responds with the relevant information. 

<a href="/course_images/ai110/your_screenshot_name.png" target="_blank"><img src='/screenshots/sample_1.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>.

2nd sample interaction:
User asks about how often their cat should be vaccinated.
The agent searches the knowledge base for the relevant information in the 'cats.txt' file and finds the relevaant information at the "CAT CARE GUIDE VACCINATION" section and responds with the relevant information.

<a href="/course_images/ai110/your_screenshot_name.png" target="_blank"><img src='/screenshots/sample_2.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>.


3rd sample interaction: 
User asks about listing all their current tasks.
The agent is able to access the users current schedule and list out the current tasks that the user has.

<a href="/course_images/ai110/your_screenshot_name.png" target="_blank"><img src='/screenshots/sample_3.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>.

# Design Decisions 
- The decision to add a knowledge base and retriever was made to be more personalized and provide more accurate information to the user. Based on the existing knowledge base, the agent would be able to provide basic information aobut the questions the owner might have about their pet. 
- The system does token matching meaning that words are treated different even if they are spelled similarly. 
- It also is designed to split the knowledge base at blank lines so that it can keep more relevant information together. The trade off to this though is that sections coulc be too long and some too short. 
- The design decision to have the agent have the ability to add tasks and list them out when requested by the user makes it more convenient for the owner to manage their schedule. The only downside would be that the ageent has to use more tools and using the API calls more often.
- The system uses different sets of .txt files as the knowledge base for different queries. The only downside is that this database of knowledge doesnt grow and the information is static. 


# Testing Summary
- At the first iteration of testing, the agent was setup to cut chunks of the knoledge base at every 150 tokens. This was not ideal because some sections of the knowledge base were too long and some were too short. So the design was changed to split the knowledge base at blank lines which allowed for more relevant information to be kept together. There was issues with certain queuries not being able to find the relevant information because of the way the knowledge base was split. 
- The second iteration of testing, the agent was then setup to cut chunks by the blanks lines which allowed for more relevant information to be kept together. The ranking in scores was also changed to only return the top 3 results to give the most relevant information. 
- I learned about how and why the token limit and how you break chunks for token matching is important and how it really affects the response the agent will give. I also learned about how important guardrails are for the agent because without them the agen will give responses that are not ideal nor make any sense. 


# Reflection 
- This project was a great learning experience for me because it allowed me to apply concepts that I have been learning about to a real world project. This also gave me the hands on experience with the lifecycle of an applied AI system from the design aspect and integrating the language model to testing and debugging through the different types of testing. 
- I also learned about the how you break up data for a RAG system matters more than I thought because it affect the response the agent will give back. The changing from chunking the token from 150 tokens to chunking by blank lines made a huge difference in the relevance of the information that the agent was able to pull from the existing knowledge base. 
- This project also taught me that guardrals are very important and not an optional thing. They are what keep the agent from going off the rails and responding to certain prompts given to it. 
- This system  gave me a better understanding of how to think about not only how should the agent respond, but also what tools does this model need and how should it use those tools and when? 
- This project made me open my mind and changed how I think about AI developement and the systems that need to be in place to make the application work as intended and provide a good user experience along with a safe and reliable system. 

# Limitations and Future Work
- Limitations of the system include the fact that the knowledge base is static and does not grow, so the information provided to the user may become outdated or may not cover all possible questions a user might have. 
- The system reads information in chunks using blank lines as separators, which may not always capture the most relevant information for a given query.
- The AI could not be misused currently but there will be more testing for potential misuse and guardrails will be added as needed.
- Future work could include implementing a more dynamic knowledge base that can be updated with new information, as well as improving the chunking method to better capture relevant information. Additionally, more guardrails could be implemented to prevent potential misuse of the system.

