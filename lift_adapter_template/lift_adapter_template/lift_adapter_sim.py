# Set up MQTT Server
import paho.mqtt.client as mqtt # Using Paho MQTT Python client
import time
class LiftSim():
    def __init__(self, IP):
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
            "lift_name": "test_lift",
            "session_id": "1234",
            "request_type": "1", 
            "destination_floor": "0", 
            "door_state": 2
        }

    # Declare IP address and port of MQTT broker
        self.IP_ADDRESS = IP
        self.PORT = 1883

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

    # The following callback methods will be called as part of the template function calls
    def get_lift_sim_current_level(self, client, userdata, msg):
        try: 
            self._lift_sim_state["current_level"] = msg.payload.decode("utf-8")
        except:
            self._lift_sim_state["current_level"] = None

    def get_lift_sim_door_state(self, client, userdata, msg):
        try: 
            self._lift_sim_state["door_state"] = msg.payload.decode("utf-8")
        except:
            self._lift_sim_state["door_state"] = None

    def set_topicsToSub(self, topicList):
        for topic in topicList:
            self._topicsToSub.append(topic)
        print("Topic List has been added")

    def publish_lift_requests_to_lift_sim(self, level, mqttClient):
        try:
            pubMsg = mqttClient.publish(topic="lift_sim/button_pressed", payload=level.encode('utf-8'), qos=1)

            #Library methods, idk what they do
            pubMsg.wait_for_publish()
            print(pubMsg.is_published())

        except Exception as e:
            print(e)

    def get_lift_requests_destination_floor(self, client, userdata, msg):
        try:
            self._lift_request["destination_floor"] = msg.payload.decode("utf-8")
            self.publish_lift_requests_to_lift_sim(self._lift_request["destination_floor"], client)
            print(f"Request to go from ")
        except:
            self._lift_request["destination_floor"] = None
    
    def attachCallbackFunctions(self):
        mqttClient.message_callback_add("lift_sim/curr_level", self.get_lift_sim_current_level)
        mqttClient.message_callback_add("lift_sim/door_state", self.get_lift_sim_door_state)
        mqttClient.message_callback_add("lift_control/interface/current_lift_state", self.get_lift_requests_destination_floor)
        
    # ----------------------------
    def check_connection(self) -> bool:
        if self._isConnected == True:
            return True
        else:
            return False

mqttClient = mqtt.Client("lift_adapter")
simulator = LiftSim("192.168.228.91")

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
    if simulator.check_connection() == False:
        print("attempting to reconnect")

#test