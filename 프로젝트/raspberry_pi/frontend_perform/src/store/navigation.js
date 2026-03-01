import { defineStore } from 'pinia';
import { Graph } from '@/utils/dijkstra';
import { calcOrientation } from '@/utils/mathUtil';
import api from '@/api';

export const useNavigationStore = defineStore('navigation', {
  state: () => ({
    graph: new Graph(),
    mapLoaded: false,
    currentLocationCode: 'STOR-001', // 초기 위치 (카트보관함)
    robotCurrentX: null,
    robotCurrentY: null,
    plannedWaypoints: [] // [추가] 계획된 경로 저장용
  }),

  actions: {
    // 현재 위치 업데이트 (수동 혹은 로직상)
    setCurrentLocation(code) {
      this.currentLocationCode = code;
    },

    // 로봇 실시간 좌표 업데이트
    updateRobotLocation({ x, y }) {
      this.robotCurrentX = x;
      this.robotCurrentY = y;

      // Keep fallback start code aligned with real robot position
      if (this.mapLoaded && this.graph && this.graph.nodes) {
        const { code, distance } = this.graph.findNearestNodeWithDistance(x, y);
        // 노드 간격이 1m일 때 스냅 임계치 0.5m
        if (code && distance <= 0.5) {
          this.currentLocationCode = code;
        }
      }
    },

    // 맵 데이터 초기화
    async initMap() {
      try {
        const res = await api.get('/map/');
        this.graph.build(res.data.nodes, res.data.links);
        this.mapLoaded = true;
      } catch (error) {
        console.error('Failed to load map data:', error);
      }
    },

    // Jetson 전송용 경로 데이터 생성 (최단 경로 기반)
    getNavigationPayload(startCode, endCode) {
      let actualStartCode = startCode;

      // 로봇의 현재 좌표가 있다면, 가장 가까운 노드를 시작점으로 변경
      if (this.robotCurrentX !== null && this.robotCurrentY !== null) {
        const nearest = this.graph.findNearestNode(this.robotCurrentX, this.robotCurrentY);
        if (nearest) {
          actualStartCode = nearest;
          console.log(`Dynamic Start Point Adjusted: ${nearest} (Based on Robot Pos: ${this.robotCurrentX.toFixed(2)}, ${this.robotCurrentY.toFixed(2)})`);
        }
      }

      const pathCodes = this.graph.findPath(actualStartCode, endCode);
      if (!pathCodes) {
        this.plannedWaypoints = [];
        return null;
      }

      const waypoints = pathCodes.map((code, index) => {
        const node = this.graph.nodes[code];
        let orientation = { z: 0.0, w: 1.0 };

        // 다음 노드 방향으로 헤딩 계산
        if (index < pathCodes.length - 1) {
          const nextNode = this.graph.nodes[pathCodes[index + 1]];
          orientation = calcOrientation(node.x, node.y, nextNode.x, nextNode.y);
        } else if (index > 0) {
          // 마지막 지점은 이전 지점의 방향 유지
          const prevNode = this.graph.nodes[pathCodes[index - 1]];
          orientation = calcOrientation(prevNode.x, prevNode.y, node.x, node.y);
        }

        return {
          code: code,
          x: node.x,
          y: node.y,
          z: orientation.z,
          w: orientation.w
        };
      });

      this.plannedWaypoints = waypoints; // [추가] 경로 저장

      return {
        command: "navigate_waypoints",
        waypoints: waypoints
      };
    }
  }
});
