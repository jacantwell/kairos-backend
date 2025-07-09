import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';

interface MapControlsProps {
  onMyLocation: () => void;
  onClearMarkers: () => void;
  markerCount: number;
}

const MapControls: React.FC<MapControlsProps> = ({
  onMyLocation,
  onClearMarkers,
  markerCount,
}) => {
  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.button} onPress={onMyLocation}>
        <Text style={styles.buttonText}>My Location</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.button} onPress={onClearMarkers}>
        <Text style={styles.buttonText}>Clear ({markerCount})</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 12,
  },
  button: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  buttonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default MapControls;