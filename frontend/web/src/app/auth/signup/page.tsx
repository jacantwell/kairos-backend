import { Configuration, DefaultApi } from "@jacantwell/kairos-api-client-ts";
import { createConfiguration } from "@jacantwell/kairos-api-client-ts";

export function createApiClient(accessToken?: string) {

    const configuration = createConfiguration();

    return new DefaultApi(configuration);;
}
