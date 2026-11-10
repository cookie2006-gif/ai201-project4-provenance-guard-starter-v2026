#!/usr/bin/env python3
"""
Criterion 4 (appeals) and the two bad bodies of criterion 5 that run_eval.py
cannot send (a JSON list and a non-JSON body). Three trials each.

    python run_criteria_extra.py --label before
"""
import argparse, json, uuid, datetime as dt
import requests
import config

URL = f"http://{config.HOST}:{config.PORT}"
TEXT = ("I went to the market on Saturday and bought way too many peaches. "
        "They were cheap, and the woman selling them gave me a bag for free. "
        "I made jam, which went badly, and then a pie, which went great.")
H = {"Content-Type": "application/json"}


def trial(n):
    out = {"trial": n, "appeals": [], "extras": {}}
    ok_status = ok_log = 0
    for i in range(10):
        r = requests.post(f"{URL}/submit", json={"text": TEXT + f" Batch {i}.", "creator_id": f"eval_appeal_{uuid.uuid4().hex[:8]}"}).json()
        cid = r["content_id"]
        a = requests.post(f"{URL}/appeal", json={"content_id": cid, "reasoning": "I wrote this myself."})
        logged = any(e.get("content_id") == cid and e.get("event") == "appeal" and e.get("status") == "under_review"
                     for e in requests.get(f"{URL}/log").json()["entries"])
        good = a.status_code == 200 and a.json().get("status") == "under_review"
        ok_status += good; ok_log += logged
        out["appeals"].append({"content_id": cid, "http": a.status_code, "body": a.json(), "logged": logged})
    out["appeals_ok"] = sum(1 for a in out["appeals"] if a["http"] == 200 and a["body"].get("status") == "under_review" and a["logged"])
    unk = requests.post(f"{URL}/appeal", json={"content_id": "does-not-exist", "reasoning": "x"})
    emp = requests.post(f"{URL}/appeal", json={"content_id": cid, "reasoning": " "})
    out["unknown_id_http"], out["empty_reasoning_http"] = unk.status_code, emp.status_code
    lst = requests.post(f"{URL}/submit", json=["a", "b"])
    raw = requests.post(f"{URL}/submit", data="this is not json")
    out["extras"] = {"json_list_http": lst.status_code, "non_json_http": raw.status_code,
                     "json_list_body": lst.json(), "non_json_body": raw.json()}
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument("--label", default=""); p.add_argument("--trials", type=int, default=3)
    args = p.parse_args()
    trials = [trial(i) for i in range(1, args.trials + 1)]
    for t in trials:
        print(f"trial {t['trial']}: appeals ok {t['appeals_ok']}/10, unknown id {t['unknown_id_http']}, "
              f"empty reasoning {t['empty_reasoning_http']}, json list {t['extras']['json_list_http']}, non-json {t['extras']['non_json_http']}")
    config.RESULTS_DIR.mkdir(exist_ok=True)
    path = config.RESULTS_DIR / f"extra_{dt.datetime.now():%Y-%m-%d_%H%M}{'_' + args.label if args.label else ''}.json"
    path.write_text(json.dumps(trials, indent=2), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
