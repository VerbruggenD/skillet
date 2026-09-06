"use client";

import { useCallback, useEffect, useRef, useState, type KeyboardEvent, type TouchEvent } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { fetchRecipe, type Ingredient, type Recipe, type Step } from "@/lib/api";

const TIMER_PRESETS_MIN = [5, 10, 15, 30];

function quantityLabel(ingredient: Ingredient): string {
  const parts = [ingredient.quantity, ingredient.unit].filter(
    (value): value is string | number => value != null && value !== "",
  );
  return parts.join(" ") || "—";
}

function formatCountdown(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function flashSweat() {
  try {
    if ("vibrate" in navigator) navigator.vibrate([240, 120, 240]);
  } catch {
    /* no op */
  }
}

function ding() {
  try {
    const AudioContextClass =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioContextClass) return;
    const ctx = new AudioContextClass();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = "sine";
    osc.frequency.value = 988;
    gain.gain.setValueAtTime(0.0001, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 1.6);
    osc.start();
    osc.stop(ctx.currentTime + 1.7);
  } catch {
    /* no op */
  }
}

type StepTimer = {
  totalSeconds: number;
  remainingSeconds: number;
  running: boolean;
  finished: boolean;
};

export default function CookPage() {
  const params = useParams<{ id: string }>();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [stepIndex, setStepIndex] = useState(0);
  const [ingredientsOpen, setIngredientsOpen] = useState(false);
  const [checked, setChecked] = useState<ReadonlySet<number>>(new Set());

  const [timer, setTimer] = useState<StepTimer | null>(null);
  const endAtRef = useRef<number | null>(null);
  const tickRef = useRef<number | null>(null);
  const touchStartX = useRef<number | null>(null);
  const touchStartY = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      setIsLoading(true);
      setError(null);
      setRecipe(null);
      try {
        const data = await fetchRecipe(Number(params.id));
        if (!cancelled) {
          setRecipe(data);
        }
      } catch {
        if (!cancelled) {
          setError("This recipe could not be found, or you don't have access to it.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [params.id]);

  const stopTimer = useCallback(() => {
    if (tickRef.current !== null) {
      window.clearInterval(tickRef.current);
      tickRef.current = null;
    }
    endAtRef.current = null;
    setTimer((current) => (current ? { ...current, running: false } : current));
  }, []);

  useEffect(() => {
    return stopTimer;
  }, [stopTimer]);

  useEffect(() => {
    let wakeLock: WakeLockSentinel | null = null;

    const requestWakeLock = async () => {
      if (typeof navigator !== "undefined" && "wakeLock" in navigator) {
        try {
          wakeLock = await navigator.wakeLock.request("screen");
        } catch {
          wakeLock = null;
        }
      }
    };

    void requestWakeLock();

    const onVisibilityChange = () => {
      if (document.visibilityState === "visible" && !wakeLock) {
        void requestWakeLock();
      }
    };
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", onVisibilityChange);
      if (wakeLock) void wakeLock.release();
    };
  }, []);

  const startTimer = useCallback(
    (seconds: number) => {
      if (tickRef.current !== null) {
        window.clearInterval(tickRef.current);
      }
      const total = Math.max(1, Math.round(seconds));
      const endAt = Date.now() + total * 1000;
      endAtRef.current = endAt;
      setTimer({ totalSeconds: total, remainingSeconds: total, running: true, finished: false });

      tickRef.current = window.setInterval(() => {
        const remaining = Math.max(0, Math.round((endAt - Date.now()) / 1000));
        setTimer({ totalSeconds: total, remainingSeconds: remaining, running: true, finished: remaining <= 0 });
        if (remaining <= 0) {
          if (tickRef.current !== null) {
            window.clearInterval(tickRef.current);
            tickRef.current = null;
          }
          ding();
          flashSweat();
        }
      }, 200);
    },
    [],
  );

  const resetTimer = useCallback(
    (minutes?: number) => {
      stopTimer();
      const total = (minutes ?? 0) * 60;
      setTimer(total > 0 ? { totalSeconds: total, remainingSeconds: total, running: false, finished: false } : null);
    },
    [stopTimer],
  );

  const nudgeTimer = useCallback(
    (deltaSeconds: number) => {
      if (timer === null || timer.running) return;
      const next = Math.max(1, timer.totalSeconds + deltaSeconds);
      setTimer({ ...timer, totalSeconds: next, remainingSeconds: next, finished: false });
    },
    [timer],
  );

  if (isLoading) {
    return (
      <div className="cook">
        <div className="cook__skeleton">Getting the stove ready…</div>
      </div>
    );
  }

  if (error || !recipe) {
    return (
      <div className="cook">
        <div className="cook__error" role="alert">
          <h1>Not on the menu</h1>
          <p>{error}</p>
          <Link className="cook__exit" href="/">
            Back to the shelf <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>
    );
  }

  const steps = [...recipe.steps].sort((a, b) => a.order - b.order);
  const currentStep: Step | undefined = steps[stepIndex];
  const totalSteps = steps.length;
  const lastStep = stepIndex >= totalSteps - 1;

  const toggleChecked = (id: number) => {
    setChecked((previous) => {
      const next = new Set(previous);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const goTo = (nextIndex: number) => {
    setStepIndex(Math.max(0, Math.min(totalSteps - 1, nextIndex)));
  };

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      goTo(stepIndex + 1);
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      goTo(stepIndex - 1);
    }
  };

  const onTouchStart = (event: TouchEvent) => {
    touchStartX.current = event.touches[0].clientX;
    touchStartY.current = event.touches[0].clientY;
  };

  const onTouchEnd = (event: TouchEvent) => {
    if (touchStartX.current === null || touchStartY.current === null) return;
    const deltaX = event.changedTouches[0].clientX - touchStartX.current;
    const deltaY = event.changedTouches[0].clientY - touchStartY.current;
    touchStartX.current = null;
    touchStartY.current = null;
    if (Math.abs(deltaX) < 60 || Math.abs(deltaX) < Math.abs(deltaY)) return;
    goTo(stepIndex + (deltaX < 0 ? 1 : -1));
  };

  const checkedCount = recipe.ingredients.filter((ingredient) => checked.has(ingredient.id)).length;

  return (
    <div
      className="cook"
      onKeyDown={onKeyDown}
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
      tabIndex={-1}
    >
      <header className="cook__header">
        <Link className="cook__exit" href={`/recipes/${recipe.id}`}>
          <span aria-hidden="true">←</span> Exit
        </Link>
        <h1 className="cook__title">{recipe.title}</h1>
        <button
          className="cook__toggle"
          type="button"
          aria-expanded={ingredientsOpen}
          onClick={() => setIngredientsOpen((open) => !open)}
        >
          {recipe.ingredients.length ? (
            <>
              Ingredients
              {checkedCount > 0 ? (
                <span className="cook__check-count" aria-label={`${checkedCount} checked`}>
                  {checkedCount}
                </span>
              ) : null}
            </>
          ) : (
            "Ingredients"
          )}
        </button>
      </header>

      <main className="cook__stage">
        {totalSteps === 0 ? (
          <div className="cook__empty">
            <h2>No steps yet</h2>
            <p>This recipe does not have any instructions to cook along to.</p>
            <Link className="cook__exit cook__exit--inline" href={`/recipes/${recipe.id}`}>
              Back to the recipe
            </Link>
          </div>
        ) : currentStep ? (
          <>
            <p className="cook__progress" aria-live="polite">
              Step {stepIndex + 1} of {totalSteps}
            </p>

            <section
              className="cook__step"
              aria-live="polite"
              aria-labelledby="cook-step-text"
              key={currentStep.id}
            >
              <p id="cook-step-text" className="cook__step-text">
                {currentStep.instruction}
              </p>
            </section>

            <div className="cook__timer">
              {timer === null ? (
                <>
                  <span className="cook__timer-label">Timer</span>
                  <div className="cook__presets">
                    {TIMER_PRESETS_MIN.map((minutes) => (
                      <button
                        className="cook__preset"
                        type="button"
                        key={minutes}
                        onClick={() => startTimer(minutes * 60)}
                      >
                        {minutes}m
                      </button>
                    ))}
                  </div>
                  <button className="cook__nudge" type="button" onClick={() => startTimer(60)}>
                    +1 min
                  </button>
                </>
              ) : (
                <>
                  <button
                    className="cook__preset"
                    type="button"
                    aria-label={timer.running ? "Pause timer" : "Resume timer"}
                    onClick={() => {
                      if (timer.running) {
                        stopTimer();
                      } else {
                        startTimer(timer.remainingSeconds);
                      }
                    }}
                  >
                    {timer.running ? "Pause" : "Resume"}
                  </button>
                  <span
                    className={`cook__countdown${timer.finished ? " cook__countdown--done" : ""}${
                      timer.running ? " cook__countdown--running" : ""
                    }`}
                    aria-live="polite"
                  >
                    {formatCountdown(timer.remainingSeconds)}
                  </span>
                  <button className="cook__nudge" type="button" onClick={() => nudgeTimer(30)}>
                    +30s
                  </button>
                  <button className="cook__nudge" type="button" onClick={() => nudgeTimer(-30)}>
                    −30s
                  </button>
                  <button className="cook__nudge" type="button" onClick={() => resetTimer()}>
                    Reset
                  </button>
                </>
              )}
            </div>

            <footer className="cook__nav">
              <button
                className="button button--ghost cook__nav-button"
                type="button"
                disabled={stepIndex === 0}
                onClick={() => goTo(stepIndex - 1)}
              >
                <span aria-hidden="true">←</span> Previous
              </button>
              {!lastStep ? (
                <button className="button cook__nav-button" type="button" onClick={() => goTo(stepIndex + 1)}>
                  Next <span aria-hidden="true">→</span>
                </button>
              ) : (
                <Link className="button cook__nav-button" href={`/recipes/${recipe.id}`}>
                  Done — back to the recipe
                </Link>
              )}
            </footer>
          </>
        ) : null}
      </main>

      {ingredientsOpen && recipe.ingredients.length ? (
        <aside className="cook__checklist" aria-label="Ingredient checklist">
          <div className="cook__checklist-head">
            <h2>Ingredients</h2>
            <button
              className="cook__close"
              type="button"
              aria-label="Close ingredient checklist"
              onClick={() => setIngredientsOpen(false)}
            >
              ×
            </button>
          </div>
          <ul className="cook__checklist-list">
            {recipe.ingredients.map((ingredient) => {
              const isChecked = checked.has(ingredient.id);
              return (
                <li key={ingredient.id}>
                  <label className={`cook__checkline${isChecked ? " cook__checkline--done" : ""}`}>
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleChecked(ingredient.id)}
                    />
                    <span className="cook__checkline-qty">{quantityLabel(ingredient)}</span>
                    <span className="cook__checkline-name">
                      {ingredient.name}
                      {ingredient.notes ? (
                        <em className="cook__checkline-notes"> · {ingredient.notes}</em>
                      ) : null}
                    </span>
                  </label>
                </li>
              );
            })}
          </ul>
        </aside>
      ) : null}
    </div>
  );
}