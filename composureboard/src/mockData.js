/**
 * Mock composition data matching the Pydantic models from orchestrator/models.py
 * 
 * Provides test data for demonstrating the composition visualization:
 * - Simple linear pipeline (3 nodes)
 * - Branching pipeline (5 nodes) 
 * - Complex pipeline (7 nodes)
 * - Massive stress-test pipeline (12 nodes)
 */

import { SERVICE_CONFIG } from './config/constants.js';

export const mockCompositions = {
  alternatives: [
    // Alternative 1: Simple Linear Pipeline (3 nodes)
    {
      description: "Simple image classification pipeline with sequential processing",
      tasks: [
        {
          task: "Image Input Processing",
          service_name: "image-preprocessor",
          id: 1,
          dep: [-1],
          args: {
            image: "input_image.jpg",
            text: null,
            document: null
          }
        },
        {
          task: "Image Enhancement",
          service_name: "stable-diffusion-x4-upscaler",
          id: 2,
          dep: [1],
          args: {
            image: "processed_image.jpg",
            text: null,
            document: null
          }
        },
        {
          task: "Image Classification",
          service_name: "resnet-50",
          id: 3,
          dep: [2],
          args: {
            image: "enhanced_image.jpg",
            text: null,
            document: null
          }
        }
      ]
    },

    // Alternative 2: Branching Pipeline (5 nodes)
    {
      description: "Multimodal analysis with parallel processing branches",
      tasks: [
        {
          task: "Document Input",
          service_name: "document-loader",
          id: 1,
          dep: [-1],
          args: {
            image: null,
            text: null,
            document: "input_document.pdf"
          }
        },
        {
          task: "Text Extraction",
          service_name: "ocr-service",
          id: 2,
          dep: [1],
          args: {
            image: null,
            text: "extracted_text",
            document: "input_document.pdf"
          }
        },
        {
          task: "Image Extraction",
          service_name: "pdf-image-extractor",
          id: 3,
          dep: [1],
          args: {
            image: "extracted_images",
            text: null,
            document: "input_document.pdf"
          }
        },
        {
          task: "Content Analysis",
          service_name: "bert-analyzer",
          id: 4,
          dep: [2, 3],
          args: {
            image: "extracted_images",
            text: "extracted_text",
            document: null
          }
        },
        {
          task: "Final Report Generation",
          service_name: "report-generator",
          id: 5,
          dep: [4],
          args: {
            image: null,
            text: "analysis_results",
            document: "final_report.pdf"
          }
        }
      ]
    },

    // Alternative 3: Complex Pipeline (7 nodes)
    {
      description: "Advanced document processing with multiple analysis branches",
      tasks: [
        {
          task: "Multi-format Input Handler",
          service_name: "universal-input-processor",
          id: 1,
          dep: [-1],
          args: {
            image: "input_images",
            text: "input_text",
            document: "input_docs"
          }
        },
        {
          task: "Text Preprocessing",
          service_name: "nlp-preprocessor",
          id: 2,
          dep: [1],
          args: {
            image: null,
            text: "raw_text",
            document: null
          }
        },
        {
          task: "Image Preprocessing",
          service_name: "cv-preprocessor",
          id: 3,
          dep: [1],
          args: {
            image: "raw_images",
            text: null,
            document: null
          }
        },
        {
          task: "Sentiment Analysis",
          service_name: "sentiment-classifier",
          id: 4,
          dep: [2],
          args: {
            image: null,
            text: "processed_text",
            document: null
          }
        },
        {
          task: "Object Detection",
          service_name: "yolov10s",
          id: 5,
          dep: [3],
          args: {
            image: "processed_images",
            text: null,
            document: null
          }
        },
        {
          task: "Cross-modal Feature Fusion",
          service_name: "multimodal-fusion",
          id: 6,
          dep: [4, 5],
          args: {
            image: "detected_objects",
            text: "sentiment_scores",
            document: null
          }
        },
        {
          task: "Insights Generation",
          service_name: "insight-generator",
          id: 7,
          dep: [6],
          args: {
            image: null,
            text: "fused_features",
            document: "insights_report.json"
          }
        }
      ]
    },

    // Alternative 4: MASSIVE Complex Pipeline (12 nodes) - Stress test!
    {
      description: "Massive multi-stage pipeline with complex dependencies (stress test composition)",
      tasks: [
        {
          task: "Data Ingestion Hub",
          service_name: "data-ingestion-service",
          id: 1,
          dep: [-1],
          args: {
            image: "batch_images",
            text: "text_corpus",
            document: "document_collection"
          }
        },
        {
          task: "Image Branch Alpha",
          service_name: "detr-resnet-101",
          id: 2,
          dep: [1],
          args: {
            image: "batch_images",
            text: null,
            document: null
          }
        },
        {
          task: "Image Branch Beta", 
          service_name: "swinv2-tiny-patch4-window16-256",
          id: 3,
          dep: [1],
          args: {
            image: "batch_images",
            text: null,
            document: null
          }
        },
        {
          task: "Text Branch Gamma",
          service_name: "bert-multilingual",
          id: 4,
          dep: [1],
          args: {
            image: null,
            text: "text_corpus",
            document: null
          }
        },
        {
          task: "Advanced Image Fusion",
          service_name: "image-fusion-transformer",
          id: 5,
          dep: [2, 3],
          args: {
            image: "fused_image_features",
            text: null,
            document: null
          }
        },
        {
          task: "Text Enhancement",
          service_name: "text-augmentation-service",
          id: 6,
          dep: [4],
          args: {
            image: null,
            text: "enhanced_text",
            document: null
          }
        },
        {
          task: "Cross-Modal Bridge A",
          service_name: "clip-vision-transformer",
          id: 7,
          dep: [5, 6],
          args: {
            image: "fused_image_features",
            text: "enhanced_text",
            document: null
          }
        },
        {
          task: "Parallel Processing Node",
          service_name: "parallel-compute-engine",
          id: 8,
          dep: [5],
          args: {
            image: "fused_image_features",
            text: null,
            document: "processing_metadata"
          }
        },
        {
          task: "Secondary Text Analysis",
          service_name: "advanced-nlp-processor",
          id: 9,
          dep: [6, 4],
          args: {
            image: null,
            text: "multi_source_text",
            document: null
          }
        },
        {
          task: "Convergence Point Alpha",
          service_name: "multi-input-aggregator",
          id: 10,
          dep: [7, 8, 9],
          args: {
            image: "aggregated_visual",
            text: "aggregated_text",
            document: "intermediate_results"
          }
        },
        {
          task: "Final Processing Stage",
          service_name: "ultimate-processor",
          id: 11,
          dep: [10],
          args: {
            image: null,
            text: "final_analysis",
            document: "comprehensive_output"
          }
        },
        {
          task: "Output Optimization",
          service_name: "result-optimizer",
          id: 12,
          dep: [11, 8], // Cross-dependency for complexity!
          args: {
            image: null,
            text: "optimized_results",
            document: "final_deliverable.json"
          }
        }
      ]
    }
  ]
};

// Helper function to convert mock data to React Flow format
export const convertToReactFlowFormat = (blueprint) => {
  const nodes = blueprint.tasks.map(task => ({
    id: task.id.toString(),
    type: 'custom',
    position: { x: 0, y: 0 }, // Will be auto-layouted
    data: {
      label: task.service_name,
      task: task.task,
      service_name: task.service_name,
      args: task.args,
      taskId: task.id
    }
  }));

  const edges = [];
  blueprint.tasks.forEach(task => {
    if (task.dep && task.dep[0] !== -1) {
      task.dep.forEach(depId => {
        edges.push({
          id: `${depId}-${task.id}`,
          source: depId.toString(),
          target: task.id.toString(),
          sourceHandle: SERVICE_CONFIG.HANDLE_IDS.OUTPUT,
          targetHandle: SERVICE_CONFIG.HANDLE_IDS.INPUT,
          type: 'smoothstep',
          animated: true
        });
      });
    }
  });

  return { nodes, edges };
};

