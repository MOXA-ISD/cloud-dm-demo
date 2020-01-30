# -*- coding: utf-8 -*-
from flask import Flask, flash, render_template, abort, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
import io, os, json
import CloudAppClass

async_mode = None

#設定 Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, path='/api/v1/rtmessage/', async_mode=async_mode)


#起始設定
# Load Configuration from file
try:
    configFile = os.path.join(os.path.dirname((os.path.dirname(os.path.abspath(__file__)))), 'config.json')
    with open(configFile) as json_file:
        config = json.load(json_file)
        _iotHubConnectionString = config['azureResource']['IoTHubConnectionString']
        _webAppURL = config['appSetting']['webAppURL']
        url = _webAppURL.split(':')
        if (len(url) > 2):
            _port = url[2].split('/')[0]
        else:
            _port = 80
        _thingsProAgentName = config['appSetting']['thingsproAgentName']        
        _rtMessageRoomId = config['appSetting']['rtMessageRoomId']
except:
    exit

_cloudApp = CloudAppClass.ThingsProEdge(_iotHubConnectionString, _thingsProAgentName)

@app.route('/api/v1/rtmessage', methods=['POST'])
def feedInMessage(): 
    postData = request.get_json(silent=True)
    roomId = postData['roomId']
    socketio.emit('onMessage', {'data': postData['data']}, room=roomId, namespace='')
    #print('Message FeedIn. Message: ' + str(postData) + ', roomId: ' + roomId)
    return 'OK'


#get /api/v1/devices
@app.route('/api/v1/devices', methods=['GET'])
def getDevices():
    _deviceList = json.dumps(_cloudApp.getThingsProEdgeList())
    return _deviceList

#get /api/v1/devices/<string:deviceId>/info
@app.route('/api/v1/devices/<string:deviceId>/info', methods=['GET'])
def getDeviceInfo(deviceId):
    deviceInfo = _cloudApp.getDeviceInfoDict(deviceId)
    if (deviceInfo != None):
        deviceInfo['deviceId'] = deviceId
        return json.dumps(deviceInfo)
    else:
        return 'None'

#get /api/v1/devices/<string:deviceId>/configuration
@app.route('/api/v1/devices/<string:deviceId>/configuration', methods=['GET'])
def getDeviceConfiguration(deviceId):
    deviceConfig = _cloudApp.getThingsProEdgeConfiguration(deviceId)
    if (deviceConfig != None):
        deviceConfig['deviceId'] = deviceId
        return json.dumps(deviceConfig)
    else:
        return 'None'

#put /api/v1/devices/<string:deviceId>/configuration
@app.route('/api/v1/devices/<string:deviceId>/configuration', methods=['PUT'])
def updateDeviceConfiguration(deviceId):
    postData = request.get_json(silent=True)
    deviceConfig = dict()
    deviceConfig['hostName'] = postData['hostName']    
    deviceConfig['description'] = postData['description']
    deviceConfig['ntpEnable'] = postData['ntpEnable']
    deviceConfig['ntpInterval'] = postData['ntpInterval']
    deviceConfig['ntpServer'] = postData['ntpServer']
    deviceConfig['timeZone'] = postData['timeZone']
    result = _cloudApp.updateThingsProEdgeConfiguration(deviceId, json.loads(json.dumps(deviceConfig)))
    print(result)
    return result

#put /api/v1/devices/<string:deviceId>/reboot
@app.route('/api/v1/devices/<string:deviceId>/reboot', methods=['PUT'])
def rebootDevice(deviceId):
    result = _cloudApp.rebootDevice(deviceId)
    #print(result)
    return result

#put /api/v1/devices/<string:deviceId>/upgrade
@app.route('/api/v1/devices/<string:deviceId>/upgrade', methods=['PUT'])
def upgradeSoftware(deviceId):
    postData = request.get_json(silent=True)
    result = _cloudApp.upgradeSoftware(deviceId, postData)
    #print(result)
    return result

#put /api/v1/devices/<string:deviceId>/enableMonitor
@app.route('/api/v1/devices/<string:deviceId>/enableMonitor', methods=['PUT'])
def monitorDeviceEnable(deviceId):
    result = _cloudApp.monitorDevice(deviceId, True)
    #print(result)
    return result

#put /api/v1/devices/<string:deviceId>/disableMonitor
@app.route('/api/v1/devices/<string:deviceId>/disableMonitor', methods=['PUT'])
def monitorDeviceDisable(deviceId):
    result = _cloudApp.monitorDevice(deviceId, False)
    #print(result)
    return result

#put /api/v1/devices/<string:deviceId>/fireAlarm
@app.route('/api/v1/devices/<string:deviceId>/fireAlarm', methods=['PUT'])
def fireAlarm(deviceId):
    result = _cloudApp.setDeviceAlarm(deviceId, True)
    #print(result)
    return result

#put /api/v1/devices/<string:deviceId>/releaseAlarm
@app.route('/api/v1/devices/<string:deviceId>/releaseAlarm', methods=['PUT'])
def releaseAlarm(deviceId):
    result = _cloudApp.setDeviceAlarm(deviceId, False)
    #print(result)
    return result

#put /api/v1/devices/<string:deviceId>/enableRemoteControl
@app.route('/api/v1/devices/<string:deviceId>/enableRemoteControl', methods=['PUT'])
def enableRemoteControl(deviceId):
    postData = request.get_json(silent=True)
    print(postData['solarControlValue'])
    result = _cloudApp.setRemoteControl(deviceId, True, postData['solarControlValue'])
    #print(result)
    return result

#put /api/v1/devices/<string:deviceId>/disableRemoteControl
@app.route('/api/v1/devices/<string:deviceId>/disableRemoteControl', methods=['PUT'])
def disableRemoteControl(deviceId):
    result = _cloudApp.setRemoteControl(deviceId, False, None)
    #print(result)
    return result

@socketio.on('join', namespace='')
def join(message):
    join_room(message['room'])
    emit('onMessage', {'data': 'In rooms: ' + ', '.join(rooms())})
    #print('Client join room. Client: ' + request.sid + ', roomId: ' + message['room'])

@socketio.on('leave', namespace='')
def leave(message):
    leave_room(message['room'])
    emit('onMessage', {'data': 'In rooms: ' + ', '.join(rooms())})
    #print('Client leave room. Client: ' + request.sid + ', roomId: ' + message['room'])

@socketio.on('disconnect_request', namespace='')
def disconnect_request():
    emit('onMessage', {'data': 'Disconnected!'})
    disconnect()


@socketio.on('my_ping', namespace='')
def ping_pong():
    emit('my_pong')


@socketio.on('connect', namespace='')
def send_connect_welcome():
    emit('onMessage', {'data': 'Welcome!'})
    #print('Client connect. Client: ' + request.sid)

@socketio.on('disconnect', namespace='')
def test_disconnect():
    print('Client disconnected. Client: ' + request.sid)

@app.route('/', methods=['GET'])
def home():    
    _deviceList = json.dumps(_cloudApp.getThingsProEdgeList())
    return render_template('index.html', deviceList=_deviceList, async_mode=socketio.async_mode, rtMessageRoomId=_rtMessageRoomId) 

if __name__ == '__main__': 
    print('Demo App is running...')
    socketio.run(app, host='0.0.0.0', port=_port, debug=True)