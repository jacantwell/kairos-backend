export interface Location {
  latitude: number;
  longitude: number;
  latitudeDelta: number;
  longitudeDelta: number;
}

export interface MarkerData {
  id: string;
  coordinate: {
    latitude: number;
    longitude: number;
  };
  title: string;
  description: string;
}

export interface PolylineData {
  id: string;
  coordinates: {
    latitude: number;
    longitude: number;
  }[];
  strokeColor: string;
  strokeWidth: number;
}