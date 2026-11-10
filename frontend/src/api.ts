import axios from 'axios';
export type Contribution={term:string;weight:number};
export type Prediction={queue:string;contributions:Contribution[]};
export type ModelRow={model:string;accuracy:number;accuracy_std:number;macro_f1:number;macro_f1_std:number;weighted_f1:number;weighted_f1_std:number};
export type DatasetAudit={raw_rows:number;english_rows:number;queue_filtered_rows:number;empty_text_removed:number;conflicting_rows_removed:number;duplicate_rows_removed:number;cleaned_rows:number;class_distribution:Record<string,number>;train_rows:number;test_rows:number;train_distribution:Record<string,number>;test_distribution:Record<string,number>};
export type TestMetrics = {
    accuracy: number;
    macro_precision: number;
    macro_recall: number;
    macro_f1: number;
    weighted_f1: number;
};

export type PerClassMetrics = Record<string, {
    precision: number;
    recall: number;
    "f1-score": number;
    support: number;
}>;

export type TunedSVM = {
    model: string;
    best_params: {
        classifier__C: number;
        classifier__class_weight: string | null;
        tfidf__min_df: number;
        tfidf__ngram_range: number[];
    };
    best_cv_macro_f1: number;
    test_metrics: TestMetrics;
    per_class: PerClassMetrics;
    confusion_matrix: number[][];
    prediction_comparison: {
        both_correct: number;
        both_wrong: number;
        fixed_by_tuning: number;
        broken_by_tuning: number;
    };
    errors: {
        ticket_text: string;
        true_queue: string;
        predicted_queue: string;
    }[];
    note: string;
};
export type Metrics={tuned_svm?: TunedSVM;selected_model:string;dataset:string;dataset_audit?:DatasetAudit;dataset_rows:number;train_rows:number;test_rows:number;labels:string[];cv_results:ModelRow[];test_metrics:{accuracy:number;macro_precision:number;macro_recall:number;macro_f1:number;weighted_f1:number};per_class:Record<string,{precision:number;recall:number;"f1-score":number;support:number}>;confusion_matrix:number[][];errors:{ticket_text:string;true_queue:string;predicted_queue:string}[]};
export const getMetrics = async (): Promise<Metrics> =>
    (await axios.get('https://helpdesk-api-ev07.onrender.com/api/metrics/')).data;export const classify=async(ticket_text:string):Promise<Prediction>=>(await axios.post('/api/classify/',{ticket_text})).data;
export const submitFeedback=async(ticket_text:string,predicted_queue:string,corrected_queue:string)=>axios.post('/api/feedback/',{ticket_text,predicted_queue,corrected_queue});
