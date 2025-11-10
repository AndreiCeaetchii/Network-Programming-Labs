/**
 * Deferred represents a Promise that can be resolved or rejected externally.
 * This is useful for implementing waiting/notification patterns.
 *
 * Example usage:
 *   const deferred = new Deferred<number>();
 *   setTimeout(() => deferred.resolve(42), 1000);
 *   const result = await deferred.promise; // waits for 1 second, then result = 42
 */
export class Deferred<T> {
    public readonly promise: Promise<T>;
    private resolveFn!: (value: T | PromiseLike<T>) => void;
    private rejectFn!: (reason?: unknown) => void;

    constructor() {
        this.promise = new Promise<T>((resolve, reject) => {
            this.resolveFn = resolve;
            this.rejectFn = reject;
        });
    }

    /**
     * Resolve this deferred promise with a value
     */
    public resolve(value: T | PromiseLike<T>): void {
        this.resolveFn(value);
    }

    /**
     * Reject this deferred promise with an error
     */
    public reject(reason?: unknown): void {
        this.rejectFn(reason);
    }
}
