import { AuthContext } from "../contexts/authContext";
import { useContext } from "react";
import { View, Text, Button } from "react-native";

export default function LoginScreen() {
  const authContext = useContext(AuthContext);

  return (
    <View>
      <Text >
        Login Screen
      </Text>
      <Button title="Log in!" onPress={authContext.logIn} />
    </View>
  );
}