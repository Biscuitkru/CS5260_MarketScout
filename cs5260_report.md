# MarketScout

---

> *[PLACEHOLDER: opening section]*

---

> *[PLACEHOLDER: system architecture overview]*

---

> *[PLACEHOLDER: the Scout]*

---

## The Analyst

The Analyst reads customer reviews and figures out what people are complaining about. By complain, it does not just look at whether a customer would like a particular product or service, or not, and instead it tries to understand deeper sentiments so that it would be more useful for the business owner. "This place has bad reviews" tells a business owner nothing. But "this place has slow service during lunch and no power outlets for laptops" is something they can actually compete against.

### What it does

The Analyst takes raw search results from Scout and extracts a list of competitors in the area and gaps where demand exists but nobody is serving it well.

For the output, we also made it structured from the start. We then pass the structured output to the Publisher since it requires clean data to build its tables and charts downstream. The structured output is also required by the conversation system as it need to reference specific competitors by field rather than trying to parse free text.

### Why structured output mattered

The Analyst returns competitors, complaints, and market gaps each as their own list with defined fields. This was particularly helpful for downstream, because if it had returned free text instead, then the Publisher, the conversation handler, and the chart builder would all have to parse the free text output.

---

## Live agent thinking on the frontend

We also built the frontend streaming, so users can watch the agents work instead of staring at a blank screen or a loading spinner, without knowing if things are working as intended.

### Why we needed this

We need this feature because a full MarketScout run takes about a minute. Without any feedback, users may assume that it is frozen. In addition, on our side during development, when something broke, we would previously had just gotten a crash with no indication of which agent caused it. However, with this addition we know exactly which part the crash had happened and we can zoom in on the specific agent.

### Two stream modes at once

We use LangGraph's `graph.stream()` with two stream modes running simultaneously: `updates` and `custom`.

The 2 stream modes have different purposes.

The custom events get emitted from inside the agents while the agents are still working. So Scout can send "searching for bubble tea shops in Taipei" as a frontend text while it is mid-search, and that message would be able to show up in the UI right away.

The update events are different from custom events. The update events only fire once when a node finishes. When Scout completes, we get back the results and show how many result groups it collected. When the Analyst completes, we show the competitor count and how many complaints and gaps it found. Publisher reports how many tables and charts it put together. So unlike the custom events that emit several times when 1 agent is working, the update events only do so once per node.

Nevertheless, the stream loop checks which type comes in and routes it:

```python
for stream_mode, chunk in graph.stream(
    input_data,
    config,
    stream_mode=["updates", "custom"],
):
    if stream_mode == "custom":

        agent = chunk.get("agent", "system")
        msg = chunk.get("msg", "")

    else:

        node = list(chunk.keys())[0]
        data = chunk[node]
```

### What the user sees

On the Streamlit side, we use nested status containers. How we achieve this, is by wrapping an outer `st.status("Researching...")` for the whole run. In addition, we also make sure that each agent gets its own collapsible container, and this container is created the first time the agent emits an event. These are all being tracked in a dictionary to ensure that duplicates does not get created.

Then, when an agent works, its container stays expanded and shows live messages. This continue until it finish running. When it finishes, we call `s.update(state="complete")` and it collapses with a green checkmark, and by the end of a run, there is a stack of green checkmarks and the report appears below.

In addition, we also added a label mapping (`AGENT_LABELS`) so the UI shows "Analyst — extracting competitors & pain points" instead of the raw node name. Without it the interface felt like a debug log and not descriptive enough from a business user point of view.

### When things break

The stream loop also sits inside a try/except, for error handling. If any agent throws an error, the outer status switches to "Pipeline failed" with a red state, and we save the error to `st.session_state`. We also preserve the pipeline context at the point of failure. Preserving the context is important, because if for example the Scout finished successfully before Analyst crashed, that finished work is not just discarded. From here, the app reruns and the user sees the failure, and this helped a lot during development because we could see exactly where in the pipeline something went wrong and what data had been collected up to that point.

### Interrupt and resume

After the stream loop finishes, we check `graph.get_state(config).next` for a pending node. If one exists, the Orchestrator hit a LangGraph `interrupt`, usually because the query was too vague (missing a business type or location, for example).

We grab the clarifying question from `state.tasks[0].interrupts[0].value`, show it as a chat message, and set `awaiting_clarification` to true. When the user replies, the pipeline resumes from the same config and picks up where it stopped. LangGraph checkpoints the state automatically, so we did not have to build persistence for this ourselves.

---

> *[PLACEHOLDER: the Publisher]*

---

> *[PLACEHOLDER: slide deck generation]*

---

> *[PLACEHOLDER: multi-turn conversation]*

---

> *[PLACEHOLDER: session persistence]*

---

