import axios from 'axios';
export type Contribution={term:string;weight:number};
export type Prediction={queue:string;contributions:Contribution[]};
export type ModelRow={model:string;accuracy:number;accuracy_std:number;macro_f1:number;macro_f1_std:number;weighted_f1:number;weighted_f1_std:number};
export type Metrics={selected_model:string;dataset:string;dataset_rows:number;train_rows:number;test_rows:number;labels:string[];cv_results:ModelRow[];test_metrics:{accuracy:number;macro_precision:number;macro_recall:number;macro_f1:number;weighted_f1:number};per_class:Record<string,{precision:number;recall:number;"f1-score":number;support:number}>;confusion_matrix:number[][];errors:{ticket_text:string;true_queue:string;predicted_queue:string}[]};
export const getMetrics=async():Promise<Metrics>=>(await axios.get('/api/metrics/')).data;
export const classify=async(ticket_text:string):Promise<Prediction>=>(await axios.post('/api/classify/',{ticket_text})).data;
export const submitFeedback=async(ticket_text:string,predicted_queue:string,corrected_queue:string)=>axios.post('/api/feedback/',{ticket_text,predicted_queue,corrected_queue});
