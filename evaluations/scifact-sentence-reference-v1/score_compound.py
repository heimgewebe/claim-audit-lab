#!/usr/bin/env python3
"""Offline audit of the exposed-case compound diagnostic. No new inference."""
import argparse, hashlib, json, pathlib, runpy
from collections import Counter

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=pathlib.Path,required=True)
    p.add_argument("--archive",type=pathlib.Path,required=True)
    p.add_argument("results",type=pathlib.Path,nargs="+")
    a=p.parse_args()
    root=a.repo/"evaluations"
    here=root/"scifact-sentence-reference-v1"
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    sci=runpy.run_path(str(root/"scifact-expert-v1/run.py"))
    pilot=runpy.run_path(str(here/"run.py"))
    compound=runpy.run_path(str(root/"scifact-compound-pilot-v1/run.py"))
    _,corpus=sci["load_release"](a.archive)
    shadow=sci["load_shadow"](); original=shadow.parse_response
    expected={str(d):("{}. Additionally, {}.".format(atoms[0][0],atoms[1][0]),compound["aggregate"]([x[1] for x in atoms])) for d,_,atoms in compound["CASES"] if d in {28419824,17333231,34747208,42404093,21287352,40234452}}
    aggregate={arm:Counter() for arm in pilot["ARMS"]}
    for path in a.results:
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        h=rows[0]
        assert h["exposed_cases"] is True
        assert h["runner_sha256"]==sha(here/"compound_diagnostic.py")
        assert h["reference_pilot_sha256"]==sha(here/"run.py")
        assert h["original_compound_sha256"]==sha(root/"scifact-compound-pilot-v1/run.py")
        assert h["archive_sha256"]==sci["RELEASE_SHA256"]
        cases={c["id"]:c for c in h["cases"]}
        assert len(cases)==6 and set(cases)==set(expected)
        assert all((c["claim"],c["operator"])==expected[k] for k,c in cases.items())
        idx={}
        print(path.name,h["model"],sha(path))
        for r in rows[1:]:
            k=r["case_id"]; arm=r["arm"]; c=cases[k]; doc=corpus[c["doc_id"]]
            ex=sci["source_text"](doc); spans=pilot["source_spans"](doc["abstract"])
            display=ex if arm=="plain" else "\n".join("[S{}] {}".format(s["id"],s["text"]) for s in spans)
            assert pilot["sha"](ex)==r["source_sha256"]==c["source_sha256"]
            assert pilot["sha"](display)==r["display_sha256"]
            shadow.INSTRUCTION=h["instructions"][arm]
            assert shadow.sha(shadow.prompt_for({"claim":c["claim"],"source_excerpt":display}))==r["prompt_sha256"]
            assert (k,arm) not in idx
            assert r["id"]==k+":"+arm
            raw=r["raw_response"]; assert pilot["sha"](raw)==r["response_sha256"]
            try:
                obj=json.loads(raw); raw_label=obj.get("label") if isinstance(obj,dict) else None
            except ValueError:
                raw_label=None
            try:
                j=pilot["reference_parse"](raw,ex,spans) if arm=="reference" else original(raw,ex)
            except ValueError:
                assert r["error"]=="invalid_output"; j=None
            else:
                assert r["status"]=="valid" and j==r["judgment"]
                assert r["localized_ids"]==(j["evidence_ids"] if arm=="reference" else pilot["quote_ids"](j["evidence_span"],ex,spans))
            strict=j["label"] if j else None
            idx[k,arm]=(raw_label,strict,r.get("localized_ids"))
            if arm=="reference":
                print(k,"reference",c["operator"],strict,[(s["id"],s["text"]) for s in (j or {}).get("evidence_spans",[])],(j or {}).get("reason"))
        assert set(idx)=={(k,a) for k in cases for a in pilot["ARMS"]}
        for arm in pilot["ARMS"]:
            rr=[r for r in rows[1:] if r["arm"]==arm]
            v=Counter(attempted=len(rr),valid=sum(idx[k,arm][1] is not None for k in cases),strict_correct=sum(idx[k,arm][1]==c["operator"] for k,c in cases.items()),raw_correct=sum(idx[k,arm][0]==c["operator"] for k,c in cases.items()),prompt_tokens=sum(r["prompt_eval_count"] for r in rr),output_tokens=sum(r["eval_count"] for r in rr))
            aggregate[arm].update(v); print(arm,dict(v))
        for k,c in cases.items():
            print(k,c["operator"],{arm:idx[k,arm] for arm in pilot["ARMS"]})
        for base in ("plain","numbered_quote"):
            print("new raw-label errors vs",base,[k for k,c in cases.items() if idx[k,base][0]==c["operator"] and idx[k,"reference"][0]!=c["operator"]])
            print("lost recognized contradictions vs",base,[k for k,c in cases.items() if c["operator"]=="contradicted" and idx[k,base][0]=="contradicted" and idx[k,"reference"][0]!="contradicted"])
    print("aggregate",json.dumps({k:dict(v) for k,v in aggregate.items()}))
if __name__=="__main__": main()
