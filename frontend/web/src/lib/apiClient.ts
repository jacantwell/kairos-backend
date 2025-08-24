import {
  createConfiguration,
  DefaultApi,
  Configuration,
} from "@jacantwell/kairos-api-client-ts";

export const createApiConfiguration = (token?: string): Configuration => {
  return createConfiguration({
    // baseServer: {
    //   url: process.env.NEXT_PUBLIC_API_BASE_URL!,
    // },
    // authMethods: {
    //   BearerAuth: token
    //     ? { tokenProvider: { getToken: () => token } }
    //     : undefined,
    // },
  });
};

export const createDefaultApi = (token?: string) =>
  new DefaultApi(createApiConfiguration(token));
