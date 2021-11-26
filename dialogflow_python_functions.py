import os
import sys
import settings
import dialogflow_v2
from google.protobuf import field_mask_pb2
from rich import print

def get_intent_id(project_id, display_name):
	try:
		intents_client = dialogflow_v2.IntentsClient()
		parent = intents_client.project_agent_path(project_id)
		intents = intents_client.list_intents(parent)
		intent_names = [
			intent.name for intent in intents if intent.display_name == display_name
		]

		intent_ids = [intent_name.split("/")[-1] for intent_name in intent_names]
		if len(intent_ids) != 0:
			return(intent_ids[0])
		else:
			return False
	except Exception as e:
		#print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
		return False    

def getIntent(project_id,intent_id):
	try:
		client = dialogflow_v2.IntentsClient()
		intent_name = client.intent_path(project_id, intent_id)
		intent = client.get_intent(intent_name, intent_view=dialogflow_v2.enums.IntentView.INTENT_VIEW_FULL)
		return intent
	except Exception as e:
		#print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
		return False

def create_intent(project_id, display_name, training_phrases_parts, message_texts):
	try:
		intents_client = dialogflow_v2.IntentsClient()
		parent = intents_client.project_agent_path(project_id)
		training_phrases = []
		for training_phrases_part in training_phrases_parts:
			part = dialogflow_v2.types.Intent.TrainingPhrase.Part(
				text=training_phrases_part)
			# Here we create a new training phrase for each provided part.
			training_phrase = dialogflow_v2.types.Intent.TrainingPhrase(parts=[part])
			training_phrases.append(training_phrase)
		text = dialogflow_v2.types.Intent.Message.Text(text=message_texts)
		message = dialogflow_v2.types.Intent.Message(text=text)
		intent = dialogflow_v2.types.Intent(
			display_name=display_name,
			training_phrases=training_phrases,
			messages=[message],
			webhook_state = 'WEBHOOK_STATE_ENABLED')
		response = intents_client.create_intent(parent, intent)
		#print('Intent created: {}'.format(response))
	except Exception as e:
		#print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
		return False    

def changeIntentName(project_id, intent_id, newName):
	try:
		client = dialogflow_v2.IntentsClient()
		intent_name = client.intent_path(project_id, intent_id)
		intent = client.get_intent(intent_name, intent_view=dialogflow_v2.enums.IntentView.INTENT_VIEW_FULL)
		intent.display_name = newName
		fieldmask = field_mask_pb2.FieldMask(paths=['display_name']) 
		response  = client.update_intent(intent, language_code='de')
		return response
	except Exception as e:
		#print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
		return False

def update_intent(project_id, intent_id, training_phrases_parts,message_texts):
	try:
		client = dialogflow_v2.IntentsClient()
		intent_name = client.intent_path(project_id, intent_id)
		intent = client.get_intent(intent_name, intent_view=dialogflow_v2.enums.IntentView.INTENT_VIEW_FULL)
		training_phrases = []
		for training_phrases_part in training_phrases_parts:
			part = dialogflow_v2.types.Intent.TrainingPhrase.Part(
				text=training_phrases_part)
			training_phrase = dialogflow_v2.types.Intent.TrainingPhrase(parts=[part])
			training_phrases.append(training_phrase)
		intent.training_phrases.extend(training_phrases) 
		intent.messages[0].text.text.append(message_texts)
		response  = client.update_intent(intent, language_code='de')
		return response
	except Exception as e:
		#print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
		return False

def delete_intent_logic(project_id, intent_id):
	try:
		#finding Intent Id
		intent_id = get_intent_id(project_id, intent_id)
		if intent_id != False:
			deleteIntent = delete_intent_function(project_id, intent_id)
			if deleteIntent != False:
				return True
			else:
				return False
		else:
			return False
	except Exception as e:
		#print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
		return False			

def delete_intent_function(project_id, intent_id):
	try:
		intents_client = dialogflow_v2.IntentsClient()
		intent_path = intents_client.intent_path(project_id, intent_id)
		response = intents_client.delete_intent(intent_path)
		
		if response == '':
			return False
		else:
			return True

	except Exception as e:
		#print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
		return False

def detect_intent_texts(project_id, session_id, text, language_code, ai = False):
	try:
		if ai != False:
			text = 'aiHello' #bypass
		#ApiConnection
		session_client = dialogflow_v2.SessionsClient()
		session = session_client.session_path(project_id, session_id)
		text_input = dialogflow_v2.types.TextInput(text=text, language_code=language_code)
		query_input = dialogflow_v2.types.QueryInput(text=text_input)
		response = session_client.detect_intent(session=session, query_input=query_input)

		if response == '':
			return False
		else:
			outcall_parameters = response.query_result.parameters
			firstPerson = dff.parameterUpdate(settings.sessionid,outcall_parameters,text) #update Parameters
			if firstPerson:
				return response	
			else:
				print(0)
				return detect_intent_texts(project_id, session_id, settings.defaultIntentFallback, language_code)
	except Exception as e:
		print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
		return False

def flowup_input(project_id, session_id, inputName, language_code):
	try:
		#ApiConnection
		session_client = dialogflow_v2.SessionsClient()
		session = session_client.session_path(project_id, session_id)
		event_input = dialogflow_v2.types.EventInput(name=inputName, language_code=language_code)
		query_input = dialogflow_v2.types.QueryInput(event=event_input)
		response = session_client.detect_intent(session=session, query_input=query_input)

		#QueryInfo
		outcall_query = response.query_result.query_text
		outcall_parameters = response.query_result.parameters

		#BotRepyInfo
		incoming_reply_id = response.response_id
		incoming_repy = response.query_result.fulfillment_text
		incoming_replies = response.query_result.fulfillment_messages

		#ContextInfo
		incoming_contexts = []
		for context in response.query_result.output_contexts:
			incoming_contexts.append(context)

		#IntentInfo
		incoming_intent = response.query_result.intent.display_name

		incoming_intent_link = response.query_result.intent.name

		incoming_intent_id = incoming_intent_link.split('projects/'+project_id+'/agent/intents/')
		incoming_intent_id = incoming_intent_id[1]

		incoming_intent_confidence = response.query_result.intent_detection_confidence

		incoming_sentiment = response.query_result.sentiment_analysis_result
		# Score between -1.0 (negative sentiment) and 1.0 (positive sentiment).

		return response
	except Exception as e:
		print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
		return False

def train_agent(project_id):
	try:
		agents_client = dialogflow_v2.AgentsClient()
		parent = dialogflow_v2.AgentsClient.project_path(project_id)
		response = agents_client.train_agent(parent)
		return response
	except Exception as e:
		#print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)
		return False

#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'your_certicate.json' #google certification
#project_id = 'your project name'

#text = 'what is your name?'
#detect_intent_texts('your project name', 'abc123', text, 'en')
#flowup_input('your project name', 'abc123', 'actionName', 'en')
#getIntent('your project name','732debaa-6680-4138-b94b-491712d3300f')
#changeIntentName('your project name','633debaa-6130-4108-b94b-493761d4300f','ladung')
#update_intent('your project name','633debaa-6610-4108-b94b-399731d3300f', ['first sentence','second sentence', '3rd sentence'], 'Nothing')
#train_agent('your project name')
#delete_intent('your project name','6a68b930-164e-4790-9c37-61ac2fc32e14')
#create_intent('your project name', 'deniz@deniz', ['first sentence', 'second sentence'], ['sample response in list form'])