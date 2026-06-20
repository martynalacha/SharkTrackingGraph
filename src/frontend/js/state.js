const State = {
  sharks: [],
  filteredSharks: [],
  selectedShark: null,
  selectedSharkTrajectory: null,
  map: null,
  zoneMarkers: [],
  trajectoryLayer: null,
  zoneTrajectoryLayers: [],
  showZones: true,
  showClusters: false,
  adminAuthed: false,
  gridPage: 0,
  gridPageSize: 30,
  gridFiltered: [],
};

let _zoneLayerGroup = null;
let _clusterLayerGroup = null;
