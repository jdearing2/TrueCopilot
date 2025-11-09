# Fly Me to the Moon 
## How to Use
Clone the repository
CD into the repository
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt 
```
and
```bash
cd app 
python3 app.py
```
or
```bash
supervisord -c supervisor/supervisord.conf
# to stop use supervisorctl -c supervisor/supervisord.conf stop all
```

## Inspiration
Have you ever been stuck, thirty minutes before the test. Brain so rotted you just wanna play clash or scroll reels; But you need to study. You need to get ready. You need to lock in.
And the best way to lock in, is to get away from everything, and go to the moon!
## What it does
Fly Me to the Moon is your personal study game when you have to cram. You give it the topic of your test, and it breaks down into simple context, providing questions and explanations to get ready for the test. It can function as a game where you are trying to go through it as fast as possible to test your skill, or you can lean back, and go through getting both vocal and text explanations of the problems as you go through it, coupled with music.
## Accessibility
For most users, I would suggest going through the topic review with the voice turned off. But the combination of an easily tab-through-able website, a vocal guide turned on by default that compliments built in features, and being a free software all assists in it being a universally beneficial project.
## How we built it
We built using Python's Flask as our web server as a basis, and then built on top, adding more features with each passing minute we had to code. We added Gemini to generate a variety of topics on the fly, adding music to make the game more engaging, ElevenLabs to have vocal assistance and increased accessibility. Supervisord and Gumicorn are being used to control  The combination of hand written code with AI integration created a wonderful project allowing us to design with precision, and make both adaptable and accessible code.
## Challenges we ran into
Git. We constantly had issues in which large files got committed while trying to work on certain parts of the project, and in the end we switched to keeping those files untracked by git, until we compressed them to include in the project.
## Accomplishments that we're proud of
Jack never built a large project - so his learning to build a project made both of us proud. Nate enjoyed the hackathon, and didn't burn himself out coding the entire time, unlike he has historically done.
## What we learned
We also both learned instruments to record the ["You Won"](https://www.youtube.com/watch?v=vQGePa3XUDI) song. Jack learned a lot about working in a large code base, and Nate practiced his skills of teaching, while also learning that you can enjoy a hackathon while still being productive.
## What's next for Fly Me to the Moon
We are going to finish adding an accounts system, work on recording an entire soundtrack to the game, adding galaxies (progressions for not just a review, but a long term plan), and then competing with friends. We considered making a linkage system with Canvas LMS - which depending on continued user feedback we will consider.
