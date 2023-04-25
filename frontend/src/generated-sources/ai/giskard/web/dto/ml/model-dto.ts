import type {ModelLanguage} from './../../../domain/ml/model-language';
import type {ModelType} from './../../../domain/ml/model-type';
import type {ProjectDTO} from './project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.ModelDTO
 */
export interface ModelDTO {
    classificationLabels: string[];
    createdDate: any /* TODO: Missing translation of java.time.Instant */;
    featureNames?: string[] | null;
    id: any /* TODO: Missing translation of java.util.UUID */;
    language: ModelLanguage;
    languageVersion: string;
    modelType: ModelType;
    name: string;
    project: ProjectDTO;
    size: number;
    threshold: number;
}