import * as ROSLIB from 'roslib';
import { JETSON_IP, JETSON_ROS_PORT } from '@/config';

class RosManager {
  constructor() {
    this.ros = null;
    this.isConnected = false;
    this.destinationTopic = null;
    this.modeTopic = null;
    this.poseTopic = null;
    this.initPoseTopic = null;
    this.statusTopic = null;
    this.poseCallback = null;
    this.statusListeners = [];

    this.connect();
  }

  connect() {
    if (this.ros) return;

    // config.js 및 .env 설정을 기반으로 접속
    this.ros = new ROSLIB.Ros({
      url: `ws://${JETSON_IP}:${JETSON_ROS_PORT}`
    });

    this.ros.on('connection', () => {
      console.log(`✅ Connected to ROS Bridge (${JETSON_ROS_PORT})`);
      this.isConnected = true;
      this.initTopics();
    });

    this.ros.on('error', (error) => {
      console.warn('❌ Error connecting to ROS Bridge:', error);
      this.isConnected = false;
    });

    this.ros.on('close', () => {
      console.log('⚠️ Connection to ROS Bridge closed.');
      this.isConnected = false;
      this.ros = null;
      setTimeout(() => this.connect(), 3000);
    });
  }

  initTopics() {
    this.destinationTopic = new ROSLIB.Topic({
      ros: this.ros,
      name: '/robot/destination',
      messageType: 'std_msgs/String'
    });

    this.modeTopic = new ROSLIB.Topic({
      ros: this.ros,
      name: '/robot/mode',
      messageType: 'std_msgs/String'
    });

    this.initPoseTopic = new ROSLIB.Topic({
      ros: this.ros,
      name: '/robot/set_init_pose',
      messageType: 'std_msgs/String'
    });

    this.statusTopic = new ROSLIB.Topic({
      ros: this.ros,
      name: '/robot/status',
      messageType: 'std_msgs/String'
    });

    this.statusTopic.subscribe((message) => {
      console.log(`[ROS Status] Received: ${message.data}`);
      this.statusListeners.forEach(callback => callback(message.data));
    });

    this.poseTopic = new ROSLIB.Topic({
      ros: this.ros,
      name: '/robot/current_pose',
      messageType: 'std_msgs/String'
    });

    this.poseTopic.subscribe((message) => {
      if (this.poseCallback) {
        try {
          const data = JSON.parse(message.data);
          this.poseCallback(data);
        } catch (e) {
          console.error('Failed to parse pose:', e);
        }
      }
    });
  }

  onStatus(callback) {
    this.statusListeners.push(callback);
  }

  onPoseUpdate(callback) {
    this.poseCallback = callback;
  }

  /**
   * [수정] new ROSLIB.Message() 대신 객체 직접 전달 방식으로 변경
   * Vite의 의존성 최적화 에러를 피하기 위한 가장 안정적인 방식입니다.
   */
  sendDestination(locationData) {
    if (!this.isConnected || !this.destinationTopic) {
      console.warn('ROS not connected.');
      return;
    }

    // 객체 형태로 직접 발행
    this.destinationTopic.publish({
      data: JSON.stringify(locationData)
    });
    console.log('🚀 Published destination (Object Mode):', locationData);
  }

  sendInitialPose(x, y) {
    if (!this.isConnected || !this.initPoseTopic) return;

    this.initPoseTopic.publish({
      data: JSON.stringify({ x: x, y: y })
    });
    console.log(`📍 Published initial pose (Object Mode): (${x}, ${y})`);
  }

  sendMode(modeStr) {
    if (!this.isConnected || !this.modeTopic) return;

    this.modeTopic.publish({
      data: modeStr
    });
    console.log(`⚙️ Published mode (Object Mode): ${modeStr}`);
  }
}

const rosManager = new RosManager();
export default rosManager;