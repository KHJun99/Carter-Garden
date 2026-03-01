export const API_URL = import.meta.env.VITE_API_URL;
export const JETSON_IP = import.meta.env.VITE_JETSON_IP;
export const JETSON_VIDEO_PORT = import.meta.env.VITE_JETSON_VIDEO_PORT;
export const JETSON_ROS_PORT = import.meta.env.VITE_JETSON_ROS_PORT;
export const TOSS_CLIENT_KEY = import.meta.env.VITE_TOSS_CLIENT_KEY;

export const MAP_INFO = {
  resolution: 0.005, // 0.05 / 10 (10x magnification)
  origin: [-4.0, -4.0, 0.0], // [x, y, z]
};