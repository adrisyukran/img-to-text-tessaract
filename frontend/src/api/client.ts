export class ApiProblem extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
  ) {
    super(message);
    this.name = "ApiProblem";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch("/api/v1" + path, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => ({
      detail: "The processing service could not complete the request.",
      code: "unexpected_error",
    }));
    throw new ApiProblem(problem.detail, response.status, problem.code);
  }
  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, init?: RequestInit) =>
    request<T>(path, { ...init, method: "POST" }),
  patch: <T>(path: string, init?: RequestInit) =>
    request<T>(path, { ...init, method: "PATCH" }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
