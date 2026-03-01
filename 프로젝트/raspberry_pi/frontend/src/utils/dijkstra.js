import { calcDistance } from './mathUtil';

export class Graph {
  constructor() {
    this.adjacencyList = {};
    this.nodes = {};
  }

  // 맵 데이터로 그래프 생성
  build(nodesData, linksData) {
    this.nodes = nodesData;
    Object.keys(nodesData).forEach(code => {
      this.adjacencyList[code] = [];
    });

    linksData.forEach(link => {
      if (this.adjacencyList[link.from] && this.adjacencyList[link.to]) {
        this.adjacencyList[link.from].push(link.to);
        this.adjacencyList[link.to].push(link.from);
      }
    });
  }

  // 가장 가까운 노드 찾기
  findNearestNode(x, y) {
    let nearestCode = null;
    let minDistance = Infinity;

    Object.entries(this.nodes).forEach(([code, node]) => {
      const dist = calcDistance(x, y, node.x, node.y);
      if (dist < minDistance) {
        minDistance = dist;
        nearestCode = code;
      }
    });

    return nearestCode;
  }

  findNearestNodeWithDistance(x, y) {
    let nearestCode = null;
    let minDistance = Infinity;

    Object.entries(this.nodes).forEach(([code, node]) => {
      const dist = calcDistance(x, y, node.x, node.y);
      if (dist < minDistance) {
        minDistance = dist;
        nearestCode = code;
      }
    });

    return { code: nearestCode, distance: minDistance };
  }

  // 최단 경로 탐색
  findPath(startCode, endCode) {
    const distances = {};
    const previous = {};
    const queue = [];

    Object.keys(this.nodes).forEach(code => {
      distances[code] = Infinity;
      previous[code] = null;
      queue.push(code);
    });
    distances[startCode] = 0;

    while (queue.length > 0) {
      queue.sort((a, b) => distances[a] - distances[b]);
      const current = queue.shift();

      if (current === endCode) {
        const path = [];
        let temp = endCode;
        while (temp) {
          path.unshift(temp);
          temp = previous[temp];
        }
        return path;
      }

      if (distances[current] === Infinity) break;

      this.adjacencyList[current].forEach(neighbor => {
        const d = calcDistance(
          this.nodes[current].x, this.nodes[current].y,
          this.nodes[neighbor].x, this.nodes[neighbor].y
        );
        const alt = distances[current] + d;

        if (alt < distances[neighbor]) {
          distances[neighbor] = alt;
          previous[neighbor] = current;
        }
      });
    }
    return null;
  }
}
