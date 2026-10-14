from typing import List, Dict, Any
from app.schemas import EmailAnalysisResult, AnalyzeEmailRequest
from app.sample_data import SAMPLE_EMAILS
from app.analyzer import analyze_email

def evaluate_single(sample: Dict[str, Any], result: EmailAnalysisResult) -> Dict[str, Any]:
    gt = sample["ground_truth"]
    
    # 1. Intent Match (Exact)
    intent_match = (result.intent.primary.lower() == gt["primary_intent"].lower())
    
    # 2. Urgency Match (Exact)
    urgency_match = (result.urgency.level.lower() == gt["urgency"].lower())
    
    # 3. Deadline Accuracy
    gt_deadlines = gt.get("expected_deadlines", [])
    res_deadlines = result.deadlines
    
    deadline_score = 1.0
    if len(gt_deadlines) > 0:
        matched_dl = 0
        for gtd in gt_deadlines:
            target_date = gtd.get("resolved_date")
            for rd in res_deadlines:
                if target_date and rd.resolved_date and (target_date in rd.resolved_date or rd.resolved_date in target_date):
                    matched_dl += 1
                    break
        deadline_score = matched_dl / len(gt_deadlines)
    else:
        deadline_score = 1.0 if len(res_deadlines) == 0 else 0.8
        
    # 4. Action Item Recall & Precision
    gt_actions = gt.get("expected_actions", [])
    res_actions = result.action_items
    
    if len(gt_actions) == 0:
        action_precision = 1.0 if len(res_actions) == 0 else 0.5
        action_recall = 1.0
    else:
        action_recall = min(1.0, len(res_actions) / len(gt_actions)) if len(gt_actions) > 0 else 1.0
        action_precision = min(1.0, len(gt_actions) / len(res_actions)) if len(res_actions) > 0 else 0.0

    # 5. Reply Quality Score (Rubric: relevance, tone, completeness, no hallucination)
    reply_quality_score = 100
    reply = result.suggested_response
    
    # Deductions
    if gt["reply_needed"] and not result.reply_needed:
        reply_quality_score -= 50
    elif not gt["reply_needed"] and result.reply_needed:
        reply_quality_score -= 40
        
    if "possible_phishing_or_scam" in gt["flags"]:
        if "possible_phishing_or_scam" not in result.flags and "possible_phishing" not in result.intent.primary:
            reply_quality_score -= 40

    if reply.body:
        # Check hallucination rules: look for placeholders like [CONFIRM: ...] when user info is missing
        if "[" in reply.body and "]" in reply.body:
            reply_quality_score += 5 # Bonus for proper placeholder use
        
    reply_quality_score = max(0, min(100, reply_quality_score))
    
    # Calculate overall score
    overall_percentage = round(
        ( (1.0 if intent_match else 0.0) * 0.25 +
          (1.0 if urgency_match else 0.0) * 0.20 +
          deadline_score * 0.20 +
          ((action_recall + action_precision) / 2) * 0.15 +
          (reply_quality_score / 100.0) * 0.20 ) * 100, 1
    )

    return {
        "id": sample["id"],
        "category": sample["category"],
        "title": sample["title"],
        "difficulty": sample["difficulty"],
        "metrics": {
            "intent_match": intent_match,
            "expected_intent": gt["primary_intent"],
            "actual_intent": result.intent.primary,
            "urgency_match": urgency_match,
            "expected_urgency": gt["urgency"],
            "actual_urgency": result.urgency.level,
            "deadline_accuracy_pct": round(deadline_score * 100, 1),
            "action_item_recall_pct": round(action_recall * 100, 1),
            "action_item_precision_pct": round(action_precision * 100, 1),
            "reply_quality_score": reply_quality_score,
            "overall_score": overall_percentage
        }
    }


def run_benchmark_suite(api_key: str = None) -> Dict[str, Any]:
    results = []
    total_score = 0.0
    intent_matches = 0
    urgency_matches = 0
    
    for sample in SAMPLE_EMAILS:
        req = AnalyzeEmailRequest(
            user_name="Alex Morgan",
            user_role="Executive Director",
            tone="professional but warm",
            signoff="Best regards,\nAlex",
            received_at=sample["email"]["received_at"],
            sender=sample["email"]["sender"],
            recipients=sample["email"]["recipients"],
            subject=sample["email"]["subject"],
            body=sample["email"]["body"],
            api_key=api_key
        )
        
        analysis_res, source = analyze_email(req)
        eval_res = evaluate_single(sample, analysis_res)
        eval_res["execution_source"] = source
        results.append(eval_res)
        
        total_score += eval_res["metrics"]["overall_score"]
        if eval_res["metrics"]["intent_match"]:
            intent_matches += 1
        if eval_res["metrics"]["urgency_match"]:
            urgency_matches += 1
            
    total_count = len(SAMPLE_EMAILS)
    avg_score = round(total_score / total_count, 1)
    
    return {
        "summary": {
            "total_emails_tested": total_count,
            "overall_accuracy_pct": avg_score,
            "intent_accuracy_pct": round((intent_matches / total_count) * 100, 1),
            "urgency_accuracy_pct": round((urgency_matches / total_count) * 100, 1),
        },
        "details": results
    }
