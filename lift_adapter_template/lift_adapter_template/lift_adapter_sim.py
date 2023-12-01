# Set up MQTT Server
import paho.mqtt.client as mqtt # Using Paho MQTT Python client
import time
import copy
class LiftSim():
    def __init__(self, IP):  
        # Declare IP address and port of MQTT broker
        self.IP_ADDRESS = IP
        self.PORT = 1883

        # States connection state with the MQTT server
        # False = Disconnected, True = Connected
        self._isConnected = False
            
        # List of topics to be subscribed, set by set_topicsToSub
        # Format: ["topic/subscription1", "topic/subscription2"]
        self._topicsToSub = []

        # Dictionary containing lift information from lift_sim
        # └── lift_sim/
        #     ├── current_level
        #     └── door_state
        self._lift_sim_state = {
            "current_level": "1",
            "door_state": "closed"
        }

        self._lift_request = {
            "lift_id": "test_lift",
            "request_id": "123456",
            "request_level": None, 
            "destination_level": None, 
        }

        # Parallel arrays
        # Queue contains the list of IDs of lift requests
        # List contains all the other info, including the request ID
        self._lift_requests_queue = []
        self._lift_requests_list = []

    def get_lift_requests_list(self):
        return self._lift_requests_queue

    def lift_queue_is_empty(self):
        if self._lift_requests_queue == []:
            return True
        else: 
            return False

    
    def resolve_lift_request(self, request_id):
        # Resolving lift request means to 
        #   1) Remove the ID from the queue
        #   2) Remove the associated data from the list

        queueIndex = self._lift_requests_queue.index(request_id)
        self._lift_requests_queue.remove(queueIndex)
        self._lift_requests_list.remove(queueIndex)
        print(f"Lift Request ID {request_id} resolved")



    # The following functions are created for the Paho MQTT Client ---------------------------

    # Assigned to client.on_connect, which runs every time the client establishes a connection with the MQTT server
    def on_connected(self, client, userdata, flags, rc):
        # Update connection state
        self._isConnected = True

        print("Connected to MQTT broker.")

    # Assigned to client.on_disconnect, which runs every time the client disconnects from the MQTT broker
    def on_disconnected(self, client, userdata, rc):
        self._isConnected = False
        print("Disconnected from MQTT broker")
    
    def subscribeToTopics(self, mqttClient):
        mqttClient.subscribe("lift_sim/curr_level")
        mqttClient.subscribe("lift_sim/door_state")
        mqttClient.subscribe("lift_control/interface/current_lift_state")

        print(f"Subscribed to topics.")

    def createNewLiftRequest(self, request_id, request_level, destination_level):
        new = self._lift_request.copy.deepcopy()
        new["request_id"] = request_id
        new["request_level"] = request_level
        new["destination_level"] = destination_level

        return new

    # The following callback methods will be called as part of the template function calls
    def get_lift_sim_current_level(self, client, userdata, msg):
        try: 
            self._lift_sim_state["current_level"] = msg.payload.decode("utf-8")
            print(f"Floor: {self._lift_sim_state['current_level']}")
        except Exception as e:
            self._lift_sim_state["current_level"] = None
            print(f"Error {e}")

    def get_lift_sim_door_state(self, client, userdata, msg):
        try: 
            self._lift_sim_state["door_state"] = msg.payload.decode("utf-8")
            print(f"Door State: {self._lift_sim_state['door_state']}")
        except Exception as e:
            print(e)
            self._lift_sim_state["door_state"] = None

    def set_topicsToSub(self, topicList):
        for topic in topicList:
            self._topicsToSub.append(topic)
        print("Topic List has been added")

    def publish_lift_requests_to_lift_sim(self, level, mqttClient):
        try:
            pubMsg = mqttClient.publish(topic="lift_sim/button_pressed", payload=level.encode('utf-8'), qos=0)
            #Library methods, idk what they do
            pubMsg.wait_for_publish()

        except Exception as e:
            print(f"Error {e} ")

    def update_lift_request_state(self, client, userdata, msg):
        try:
            info = msg.payload.decode("utf-8")
            allInfo =  info.split(";")
            if allInfo[1] not in self._lift_requests_queue:
                newLiftRequest = createNewLiftRequest(allInfo[1], allInfo[2], allInfo[3])
                self._lift_requests_list.append(newLiftRequest)
                print(f"New Request queued. \nID: {allInfo{1}} \nRequest Floor: {allInfo[2]} \nDestination Floor:{allInfo[3]}")
        except Exception as e:
            print(f"Error {e}")
    
    def attachCallbackFunctions(self):
        mqttClient.message_callback_add("lift_sim/curr_level", self.get_lift_sim_current_level)
        mqttClient.message_callback_add("lift_sim/door_state", self.get_lift_sim_door_state)
        mqttClient.message_callback_add("lift_control/interface/current_lift_state", self.update_lift_request_state)
        
    # ----------------------------
    def check_connection(self) -> bool:
        if self._isConnected == True:
            return True
        else:
            return False

mqttClient = mqtt.Client("lift_adapter")
simulator = LiftSim("192.168.18.3")

def publish_lift_state_update():
    requestData = simulator.get_lift_requests_list()
    simulator.publish_lift_requests_to_lift_sim(simulator.requestData["request_level"], mqttClient)
    simulator.publish_lift_requests_to_lift_sim(simulator.request["destination_level"], mqttClient)
    simulator.resolve_lift_request(requestData["request_id"])
    print("Message successfully published. Lift request queue updated.")
    
# Run set-up Commands
mqttClient.on_connect = simulator.on_connected
mqttClient.on_disconnect = simulator.on_disconnected
simulator.attachCallbackFunctions()
mqttClient.connect(simulator.IP_ADDRESS, simulator.PORT)
# STart a new loop
mqttClient.loop_start()
simulator.subscribeToTopics(mqttClient)
while True:
    time.sleep(2)
    print("loop")
    if simulator.lift_queue_is_empty() == False:
        publish_lift_state_update()
    if simulator.check_connection() == False:
        print("attempting to reconnect")
   #  simulator.publish_lift_requests_to_lift_sim("7", mqttClient)

#test
