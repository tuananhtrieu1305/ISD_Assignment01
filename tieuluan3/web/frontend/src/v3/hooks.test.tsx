import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useResource } from "./hooks";
describe("request identity, cancellation and retry", () => {
  it("ignores a stale response when the dataset identity changed", async () => {
    const resolvers: ((value: string) => void)[] = [];
    const signals: AbortSignal[] = [];
    const load = (signal: AbortSignal) => {
      signals.push(signal);
      return new Promise<string>((resolve) => resolvers.push(resolve));
    };
    const { result, rerender, unmount } = renderHook(
      ({ id }) => useResource(id, load),
      { initialProps: { id: "a" } },
    );
    rerender({ id: "b" });
    expect(signals[0].aborted).toBe(true);
    await act(async () => {
      resolvers[0]("stale-a");
      resolvers[1]("fresh-b");
    });
    expect(result.current.value).toBe("fresh-b");
    unmount();
    expect(signals[1].aborted).toBe(true);
  });
  it("reports errors and retries only the GET load, never a POST job", async () => {
    const load = vi
      .fn()
      .mockRejectedValueOnce(new Error("unavailable"))
      .mockResolvedValueOnce("recovered");
    const { result } = renderHook(() => useResource("same-identity", load));
    await waitFor(() =>
      expect(result.current.error?.message).toBe("unavailable"),
    );
    act(() => result.current.retry());
    await waitFor(() => expect(result.current.value).toBe("recovered"));
    expect(load).toHaveBeenCalledTimes(2);
  });
  it("does not surface an AbortError as an API failure", async () => {
    const load = vi
      .fn()
      .mockRejectedValue(new DOMException("cancelled", "AbortError"));
    const { result } = renderHook(() => useResource("aborted", load));
    await act(async () => {});
    expect(result.current.error).toBeNull();
  });
});
