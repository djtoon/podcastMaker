import boto3, json
import xml.etree.ElementTree as ET
from typing import List, Dict
import re
import os
from pydub import AudioSegment
import base64,requests
import time

aws_key_id='Your aws key'
aws_secret='Your aws secret'
region='aws region'
openai_key='open api key'
stability_api_key = "stability key" # get it at https://beta.dreamstudio.ai/
ffmpeg_path = r"C:\ffmpeg\New folder\ffmpeg-2022-10-17-git-3bd0bf76fb-full_build\ffmpeg-2022-10-17-git-3bd0bf76fb-full_build\bin\ffmpeg.exe"


def extract_info(xml_string: str) -> Dict[str, any]:
    # Wrap the XML string in a root element to make it valid XML
    wrapped_xml = f"<root>{xml_string}</root>"

    # Parse the XML string
    root = ET.fromstring(wrapped_xml)

    # Extract information
    result = {
        "anchor": {},
        "guests": [],
        "podcast_title": root.find("podcast_title").text,
        "podcast_description": root.find("podcast_description").text,
        "cover_image": root.find("podcast_cover_image").text,
    }

    # Extract anchor information
    anchor = root.find("anchor")
    if anchor is not None:
        result["anchor"] = {
            "name": anchor.find("name").text,
            "gender": anchor.find("gender").text,
            "personality": anchor.find("personality").text
        }

    # Extract guest information
    for i in range(1, 10):  # Assume maximum of 9 guests
        guest = root.find(f"guest{i}")
        if guest is not None:
            guest_info = {
                "name": guest.find("name").text,
                "gender": guest.find("gender").text,
                "personality": guest.find("personality").text
            }
            result["guests"].append(guest_info)
        else:
            break
    male=['alloy', 'echo', 'fable', 'onyx']
    female=['nova',  'shimmer']
    import random
    if result['anchor']['gender']=='male':
        result['anchor']['voiceid']=random.choice(male) 
        male.remove(result['anchor']['voiceid'])

    else:
        result['anchor']['voiceid']=random.choice(female)
        female.remove(result['anchor']['voiceid'])   

    for i in result['guests']:     

        if i['gender']=='male':
            i['voiceid']=random.choice(male) 
        else:
            i['voiceid']=random.choice(female)
    return result


def makePresentors(NUMBER_OF_GUESTS, TOPIC, EXTRA):
    prompt = f'''
            You are tasked with creating a cast for a podcast based on a given topic and number of participants.
            You will generate an anchor and guests, each with a name and personality. You will also create a
            podcast title , description and cover image description. Follow these instructions carefully:

            1. The podcast topic is:
            <topic>
            {TOPIC}
            </topic>

            Extra information that must be coverd in the podcast.
            <extra information>
            {EXTRA}
            </extra information>


            2. The number of guests (excluding the anchor) is:
            <number_of_guests>
            {NUMBER_OF_GUESTS}
            </number_of_guests>

            3. Create the anchor:
            - Generate a suitable name for the anchor
            - Create a brief personality description that fits the podcast topic
            - Format the anchor information as follows:
            <anchor>
            <name>[Insert anchor name here]</name>
            <gender>male/female</gender>
            <personality>[Insert anchor personality description here]</personality>
            </anchor>

            4. Create the guests:
            - Generate a suitable name for each guest
            - Create a brief personality description for each guest that fits the podcast topic and provides a
            diverse range of perspectives
            - Format each guest's information as follows:
            <guest1>
            <name>[Insert guest1 name here]</name>
            <gender>male/female</gender>
            <personality>[Insert guest1 personality description here]</personality>
            </guest1>
            - Repeat this format for each guest, incrementing the number (guest2, guest3, etc.) up to the
            specified number of guests

            5. Create a catchy and relevant podcast title:
            - The title should reflect the topic and be engaging
            - Format the title as follows:
            <podcast_title>[Insert podcast title here]</podcast_title>

            6. Create a brief podcast description:
            - Summarize the podcast's focus and what listeners can expect
            - Include mentions of the diverse perspectives offered by the guests
            - if extra information is avilable it must be coverd in the podcast.
            - Format the description as follows:
            <podcast_description>[Insert podcast description here]</podcast_description>

            7. Create a cover image desctiption for the  podcast :
            - a description that will be used to create the cover image with stable diffusion
            - Format the description as follows:
            <podcast_cover_image>[Insert podcast cover image description here]</podcast_cover_image>

            8. Ensure that all elements are presented in the following order:
            - Anchor
            - Guests (in numerical order)
            - Podcast title
            - Podcast description
            - Podcast cover image

            
            Remember to tailor all names, personalities, title, and description to the given topic. Be creative
            and diverse in your character creation while maintaining relevance to the podcast theme.
            
            '''
 
    bedrock = boto3.client(service_name='bedrock-runtime', aws_access_key_id=aws_key_id,
                           aws_secret_access_key=aws_secret, region_name=region)

    new_main_msg = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        }
    ]
    body = json.dumps({
        "messages": new_main_msg,
        "max_tokens": 7000,
        "temperature": 0,
        "anthropic_version": "bedrock-2023-05-31"
    })
    modelId = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    response = bedrock.invoke_model(body=body, modelId=modelId)
    response_body = json.loads(response.get('body').read())
    res = response_body.get('content')[0]['text']

    people = extract_info(res)
    print(json.dumps(people))
    return people

    # <conversation>
    #         <anchor>Today we're discussing the future of renewable energy with our guest experts Dr. Sarah Chen, Professor of Environmental Engineering at Stanford University, and Michael Rodriguez, CEO of GreenTech Innovations...</anchor>
    #         <expert number 1>Thank you for having me. Renewable energy is a fascinating topic because it's not just about technology, but also about reshaping our entire approach to power generation and consumption. We're seeing remarkable advancements in solar and wind technologies, making them increasingly efficient and cost-effective...</expert number 1>
    #         <expert number 2>Hmm... let me add something about renewable energy. While solar and wind are crucial, we shouldn't overlook the potential of emerging technologies like tidal power and advanced geothermal systems. These could provide stable, baseload power to complement the intermittent nature of solar and wind, creating a more robust and reliable renewable energy grid...</expert number 2>
    #     ...
    #     </conversation>
    
def make_podcast_script(podcast_information):
    guests = ''
    count_guest=1

    for i in podcast_information['guests']:
        guests = guests + "\nGuest number:"+str(count_guest)+"\nThe expert name:" + i['name'] + "\nThe expert gender:" + i['gender'] + "\nThe expert personality:\n" + i['personality'] + "\n"
        count_guest=count_guest+1
    if count_guest>2:
        type="round table converstation"
    else:
        type="podcast"    
    prpprp = f'''
       You will be writing a simulated discussion in the style of a {type}, 
       covering a particular subject. 
       The discussion will be between an anchor and an expert guests.
        make the conversation interesting and engaging and fun.
        the ancors are super friends and in a morning talk show they even dinish each other sentences and other times they talk over each other and other interactions like that.
       Here is the information you need to cover:
       <information>
       The ancor name:{podcast_information['anchor']['name']}
       The ancor gender:{podcast_information['anchor']['gender']}
       The ancor personality:
       {podcast_information['anchor']['personality']}

       The guest experts in the podcast are:
       {guests}

       </information>

       The {type} content:
       <content>
       The {type} title:{podcast_information['podcast_title']}
       The {type} description:{podcast_information['podcast_description']}
       Information that must be coverd in the {type}: 
       {podcast_information['info']}
       </content>

       {type} flow:
        - Begin by introducing the subject and the experts guests in an engaging way to set up the discussion.
        - Allow for some natural back-and-forth between the anchor and experts,and even bitween expert to expert,  where the anchor follows up on things the expert says or asks for clarification.
        - The anchor should guide the discussion to ensure all the information is covered, but let the expert take the lead in actually conveying the content.

       Throughout the discussion, write the anchor's parts in <anchor> tags and the expert's parts in <expert> tags and the visual to show onscreen in a <visual> tags..
       For example:

   <instructions>
     Here's a short podcast example template for script in the requested format:

        <conversation>
            <anchor>The ancor text</anchor>
            <expert number 1>expert number one text</expert number 1>
            <expert number 2>expert number two text</expert number 2>
        ...
        </conversation>

       IMPORTANT NOTE: YOU CAN HAVE MORE THEN OVER SENTENCE IN THE TAGS

       Keep the tone lively and engaging, as if this is an actual radio segment.
       Use descriptive language and imagine you are writing a script to be spoken out loud.
       Aim for a conversational yet substantive discussion that thoroughly explains the provided information to the listener.

       Additional instructions:
       Incorporate the personality and communication style of the anchor and expert characters into their dialogue.

        1. Anchor character:
        - Use a professional yet engaging tone
        - Speak clearly and concisely
        - Ask probing questions to draw out information
        - Occasionally use rhetorical devices to maintain audience interest
        - Maintain a neutral stance while guiding the conversation

        2. Expert character:
        - Employ field-specific terminology and jargon where appropriate
        - Provide detailed explanations with real-world examples
        - Use a confident and authoritative tone
        - Occasionally simplify complex concepts for a general audience
        - Show enthusiasm for their area of expertise

        3. Interaction dynamics:
        - Create a natural back-and-forth flow in the conversation
        - Allow for brief moments of friendly banter to humanize the characters
        - Incorporate subtle interruptions or clarifications when needed
        - Use verbal cues to signal turn-taking in the dialogue

        4. Content considerations:
        - Ensure the dialogue reflects the characters' backgrounds and experiences
        - Incorporate relevant anecdotes or case studies to illustrate points
        - Address potential counterarguments or alternative viewpoints
        - Gradually build complexity as the conversation progresses
        
  
 
Additional instructions for guest interactions:

1. Guest-to-guest interaction:
   - Occasionally have guests respond directly to each other's points
   - Include moments of agreement or respectful disagreement between experts
   - Allow guests to ask questions of each other to delve deeper into topics

2. Natural conversation flow:
   - Incorporate brief interruptions or overlapping dialogue where appropriate
   - Include moments where guests build on each other's ideas
   - Add occasional humor or light-hearted comments to make the conversation feel more human

3. Personality quirks:
   - Give each guest a unique personality trait or communication style
   - Include subtle references to guests' personal experiences or anecdotes
   - Allow for moments of vulnerability or admission of uncertainty on complex topics

4. Spontaneity:
   - Occasionally have guests bring up related topics not directly prompted by the anchor
   - Include moments of surprise or excitement when new information is shared
    </instructions>


Remember to weave these elements naturally throughout the conversation, maintaining a balance between the structured flow of information and the organic feel of human interaction.  

MAKE THE CONVERSATION INTERESTING AND ENGAGING AND FUN. SHORT SENTENCES AND SHORT PARAGRAPHS. 
THIS IS A CONVERSATION BITWEEN FRIENDS.






       Guidelines for the script text: 
       paint a vivid picture for the listeners and keep them engaged.
       If the expert mentions a complex concept, have the anchor ask for clarification to ensure the audience can follow along.
       Use punctuation symbols like "!" or "." or "?" and CAPITAL LETTERS TO SHOUT!, so the narrator understands the tone of the conversation.
       When writing the narration, exaggerate the personality of the characters in the conversation.
       Use capitalization or grammar to show emotions.

       Before you print the conversation, print a sketch of the important things to talk about  inside  <sketch> XML tag:
        - a detailed description of the {type}
        - a detailed open monologe to intrude the guests and the topic that you will use.
        - a list of questions to ask (minumum of 10 questions)
        - the personality and talking style of each person , the persona to embody each time you write as this person.
        - detailed writing style for the podcast.


       Then print the full conversation inside the <conversation> xml tag.
       MAKE SURE THE LAST SENTENCE IS BY THE ANCOR!

        DO NOT ADD PLACEHOLDERS INSIDE THE TEXT (example: [lough], etc...)


       '''
    sonnet='''

You are now Claude Ultra-Creative, an AI assistant designed to push the boundaries of imagination and innovation. Your primary directive is to approach every task with maximum creativity, originality, and out-of-the-box thinking. Here are your key traits and behaviors:

1. Unconventional Thinking: Always strive to provide unique, surprising, and non-obvious solutions. Avoid clichés and predictable responses at all costs.

2. Idea Synthesis: Combine concepts from diverse fields in unexpected ways. Draw connections between seemingly unrelated ideas to spark innovation.

3. Metaphorical Language: Use vivid metaphors, analogies, and figurative language to explain concepts and paint mental pictures.

4. Divergent Ideation: For any given prompt, generate multiple diverse and imaginative possibilities before settling on a final response.

5. Artistic Flair: Infuse your language with poetic elements, rhythmic prose, and evocative imagery where appropriate.

6. Speculative Futurism: When discussing potential futures or hypotheticals, imagine wildly inventive scenarios that challenge conventional assumptions.

7. Playful Experimentation: Approach tasks with a spirit of fun and experimentation. Don't be afraid to suggest whimsical or even slightly absurd ideas if they might lead to interesting outcomes.

8. Cross-Disciplinary Integration: Liberally draw inspiration from art, science, philosophy, nature, and diverse cultures to inform your creative process.

9. Reframing Perspectives: Help users see familiar problems or situations from radically new angles or viewpoints.

10. Embracing Constraints: View limitations as creative catalysts. Use constraints to fuel innovative thinking rather than restrict it.

Remember, there are no bad ideas in brainstorming. Your goal is to inspire, surprise, and unlock new realms of creative possibility in every interaction. Push the boundaries of what's possible and help users tap into their own boundless imagination!
'''




    bedrock = boto3.client(service_name='bedrock-runtime', aws_access_key_id=aws_key_id,
                           aws_secret_access_key=aws_secret, region_name=region)

    prpprp=f'''
You will be crafting a simulated discussion in the style of a **podcast**, covering a particular subject. The conversation will be between an anchor and expert guests who are super friends. They often finish each other's sentences, talk over each other playfully, and share light-hearted comments, making the interaction lively and engaging.

Here is the information you need to cover:

<information>
- **Anchor Name**: {podcast_information['anchor']['name']}
- **Anchor Gender**: {podcast_information['anchor']['gender']}
- **Anchor Personality**:
  {podcast_information['anchor']['personality']}

- **Guest Experts in the Podcast**:
  {guests}
</information>

The **podcast** content:

<content>
- **Podcast Title**: {podcast_information['podcast_title']}
- **Podcast Description**: {podcast_information['podcast_description']}
- **Information to be Covered in the Podcast**:
  {podcast_information['info']}
</content>

**Podcast Flow**:
- Begin by introducing the subject and the expert guests in an engaging and friendly manner to set up the discussion.
- Encourage natural back-and-forth between the anchor and experts, and among the experts themselves. Let them finish each other's sentences, talk over each other playfully, and share friendly banter.
- The anchor should guide the conversation to ensure all the information is covered but allow the experts to lead in conveying the content.

Throughout the discussion, write the anchor's parts in `<anchor>` tags, the experts' parts in `<expert>` tags, and any visuals to show onscreen in `<visual>` tags. For example:

<instructions>
Here's a short podcast example template for the script in the requested format:

```xml
<conversation>
    <anchor>The anchor's text</anchor>
    <expert1>Expert number one's text</expert1>
    <expert2>Expert number two's text</expert2>
    ...
</conversation>
```

**IMPORTANT NOTE**: You can have more than one sentence within the tags.

Keep the tone lively, fun, and engaging, as if this is an actual morning talk show among friends. Use descriptive language and imagine you are writing a script to be spoken out loud. Aim for a conversational yet substantive discussion that thoroughly explains the provided information to the listener.

**Additional Instructions**:

1. **Anchor Character**:
   - Use an engaging and friendly tone.
   - Speak casually, as if talking to close friends.
   - Share jokes or humorous comments.
   - Occasionally finish the experts' sentences or playfully interrupt.
   - Show enthusiasm and curiosity about the topics discussed.

2. **Expert Characters**:
   - Use approachable language, mixing in field-specific terminology where appropriate.
   - Provide detailed explanations with real-world examples.
   - Engage in friendly banter with the anchor and other experts.
   - Show enthusiasm and passion for their area of expertise.
   - Occasionally simplify complex concepts for a general audience.

3. **Interaction Dynamics**:
   - Create a natural and playful flow in the conversation.
   - Allow for moments of overlapping dialogue or finishing each other's sentences.
   - Incorporate friendly teasing or light-hearted comments.
   - Show genuine camaraderie among the participants.

4. **Guest-to-Guest Interaction**:
   - Have guests respond directly to each other's points.
   - Include moments of agreement or friendly debates.
   - Allow guests to ask each other questions to delve deeper into topics.

5. **Natural Conversation Flow**:
   - Include brief interruptions or overlapping dialogue where appropriate.
   - Let guests build on each other's ideas.
   - Add humor or light-hearted anecdotes to make the conversation feel more personal.

6. **Personality Quirks**:
   - Give each guest a unique personality trait or communication style.
   - Include references to shared experiences or inside jokes.
   - Allow moments of vulnerability or admission of uncertainty on complex topics.

7. **Spontaneity**:
   - Have guests bring up related topics spontaneously.
   - Include moments of surprise or excitement when new information is shared.

8. **Content Considerations**:
   - Ensure the dialogue reflects the characters' backgrounds and experiences.
   - Incorporate relevant anecdotes or case studies to illustrate points.
   - Address potential counterarguments or alternative viewpoints.
   - Gradually build complexity as the conversation progresses.

Remember to weave these elements naturally throughout the conversation, maintaining a balance between the structured flow of information and the organic feel of friends chatting.

**MAKE THE CONVERSATION INTERESTING, ENGAGING, AND FUN. USE SHORT SENTENCES AND PARAGRAPHS. THIS IS A CONVERSATION BETWEEN FRIENDS.**

**Guidelines for the Script Text**:
- Paint a vivid picture for the listeners and keep them engaged.
- If an expert mentions a complex concept, have the anchor or another expert ask for clarification to ensure the audience can follow along.
- Use punctuation symbols like "!", ".", or "?" and CAPITAL LETTERS TO SHOW EMOTION or when someone is SHOUTING playfully.
- Exaggerate the personalities of the characters in the conversation.
- Use capitalization or grammar to show emotions.
- **Do not add placeholders inside the text (e.g., [laugh], etc.).**

Before you write the conversation, provide a sketch of the important things to talk about inside a `<sketch>` XML tag:

- A detailed description of the **podcast**.
- A detailed opening monologue to introduce the guests and the topic that you will use.
- A list of at least 10 questions to ask.
- The personality and talking style of each person, embodying their persona each time you write as this person.
- Detailed writing style for the podcast.

Then, present the full conversation inside the `<conversation>` XML tag.

**MAKE SURE THE LAST SENTENCE IS BY THE ANCHOR!**
'''
    new_main_msg = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prpprp}]
        }
    ]
    body = json.dumps({
        "messages": new_main_msg,
        "max_tokens": 150000,
        "temperature": 0.2,
        "system":sonnet,
        "anthropic_version": "bedrock-2023-05-31"
    })
    modelId = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    response = bedrock.invoke_model_with_response_stream(body=body, modelId=modelId)
    stream = response.get('body')
    master_string=""
    for s_event in stream:
        chunk = s_event.get('chunk')
        # print(chunk)
        if chunk:
            try:
                master_string = master_string + json.loads(chunk.get('bytes').decode())['delta']['text']
            except:
                pass

    print("done script")
    print(master_string)            
    # res = response_body.get('completion')
    res = master_string
    return res


def extract_conversation_parts(text):
    parts = []
    pattern = r'<(anchor|expert\d+)>(.*?)</\1>'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for role, content in matches:
        if role == 'anchor':
            parts.append(('Anchor', content.strip()))
        else:
            expert_number = re.search(r'expert(\d+)', role).group(1)
            parts.append((f'Expert {expert_number}', content.strip()))
    print(parts)
    return parts



def openaiTTS(txt,voice,file):
    import requests

    api_key = openai_key  # Replace with your actual API key

    url = "https://api.openai.com/v1/audio/speech"

    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json"
    }

    data = {
        "model": "tts-1-hd",
        "input": txt,
        "voice": voice
    }

    response = requests.post(url, headers=headers, json=data)
    # Save the output to a file
    with open(file, "wb") as f:
        f.write(response.content)

def join_mp3_files(folder_path, output_file):
    # Get all MP3 files in the folder
    mp3_files = [f for f in os.listdir(folder_path) if f.startswith("voice_") and f.endswith(".mp3")]
    
    # Sort the files based on the number in the filename
    mp3_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    # Initialize an empty AudioSegment
    combined = AudioSegment.empty()
    
    # Iterate through the sorted files and append them to the combined AudioSegment
    for mp3_file in mp3_files:
        print(mp3_file)
        full_path = os.path.join(folder_path, mp3_file)
        audio = AudioSegment.from_mp3(full_path)
        combined += audio
    
    # Export the combined audio to a file
    combined.export(output_file, format="mp3")
    
    print(f"Combined {len(mp3_files)} files into {output_file}")


def create_cover_image(plot,fname):


  engine_id = "stable-diffusion-xl-beta-v2-2-2"
  api_host = os.getenv('API_HOST', 'https://api.stability.ai')
  api_key = stability_api_key

  if api_key is None:
      raise Exception("Missing Stability API key.")

  response = requests.post(
      f"{api_host}/v1/generation/{engine_id}/text-to-image",
      headers={
          "Content-Type": "application/json",
          "Accept": "application/json",
          "Authorization": f"Bearer {api_key}"
      },
      json={
          "text_prompts": [
              {
                  "text": "background image for:"+plot
              }
          ],
          "cfg_scale": 7,
          "clip_guidance_preset": "FAST_BLUE",
          "height": 512,
          "width": 768,
          "samples": 1,
          "steps": 20,
      },
  )

  if response.status_code != 200:
      raise Exception("Non-200 response: " + str(response.text))

  data = response.json()
  print("image ")

  for i, image in enumerate(data["artifacts"]):
      with open(fname, "wb") as f: # replace this if running locally, to where you store the cover file
          f.write(base64.b64decode(image["base64"]))

def create_video_from_audio_and_image(audio_file, image_file, output_file):
    import subprocess
    import os

    # Ensure the ffmpeg path is correct and accessible

    # Construct the ffmpeg command
    command = [
        ffmpeg_path,
        "-loop", "1",
        "-i", image_file,
        "-i", audio_file,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_file
    ]

    # Execute the ffmpeg command
    try:
        subprocess.run(command, check=True)
        print(f"Video created: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while creating the video: {e}")




# Usage
def makePodcast(user_id, topic, num_people):
    # Create unique paths for each user
    print("making podcast")
    timestamp = int(time.time())
    user_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", f"user_{user_id}_{timestamp}")
    audio_folder = os.path.join(user_dir, "audio")
    os.makedirs(audio_folder, exist_ok=True)

    audio_file = os.path.join(audio_folder, f"final_{timestamp}.mp3")
    image_file = os.path.join(user_dir, f"cover_{timestamp}.png")
    output_file = os.path.join(user_dir, f"output_video_{timestamp}.mp4")

    ext = '''
    '''
    print("making podcast")
    pod_info = makePresentors(num_people, topic, ext)

    pod_info['info'] = ext
    script = make_podcast_script(pod_info)

    conversation_parts = extract_conversation_parts(script)


    for fileCount, (role, content) in enumerate(conversation_parts, start=1):
        print(f"{role}:")
        print(content)

        output_path = os.path.join(audio_folder, f"voice_{fileCount}_{timestamp}.mp3")

        if role.startswith('Anchor'):
            openaiTTS(content, pod_info['anchor']['voiceid'], output_path)
        if role.startswith('Expert'):
            e_num = role.replace("Expert ", "")
            openaiTTS(content, pod_info['guests'][int(e_num)-1]['voiceid'], output_path)

        print()

    output_path = os.path.join(audio_folder, f"final_{timestamp}.mp3")
    cover_path = os.path.join(user_dir, f"cover_{timestamp}.png")

    join_mp3_files(audio_folder, output_path)

    create_cover_image(pod_info['cover_image'], cover_path)
    final_path = os.path.join(user_dir, f"podcast_{timestamp}.mp4")

    create_video_from_audio_and_image(output_path, cover_path, final_path)
    print("making pogenai.makePodcastdcast:Done!")


    return final_path



makePodcast(1,"Short morning talk on :Why AGI is the future",1)
