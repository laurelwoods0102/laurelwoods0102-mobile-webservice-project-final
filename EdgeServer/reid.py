import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class PersonReIDSystem:
    def __init__(self):
        # Force CPU if CUDA is not reliable in your container
        self.device = torch.device("cpu") 
        
        # Load pre-trained ResNet
        self.model = models.resnet18(pretrained=True)
        self.model.fc = nn.Identity()  # Remove classification layer
        self.model.to(self.device)
        self.model.eval()
        
        self.preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                                 std=[0.229, 0.224, 0.225]),
        ])

    def get_embedding(self, img_path, bbox):
        try:
            # Load Image
            full_img = Image.open(img_path).convert('RGB')
            
            # Crop Person using BBox [xmin, ymin, xmax, ymax]
            # Ensure bbox is within image bounds
            width, height = full_img.size
            xmin = max(0, bbox[0])
            ymin = max(0, bbox[1])
            xmax = min(width, bbox[2])
            ymax = min(height, bbox[3])
            
            if xmax - xmin < 10 or ymax - ymin < 10:
                return None, None # Skip tiny/invalid crops

            person_crop = full_img.crop((xmin, ymin, xmax, ymax))
            
            # Extract Features
            tensor = self.preprocess(person_crop).unsqueeze(0).to(self.device)
            with torch.no_grad():
                feat = self.model(tensor)
            
            return feat.cpu().numpy().flatten(), person_crop
        except Exception as e:
            print(f"[ReID] Error extracting features: {e}")
            return None, None

    def group_people(self, person_data, threshold=0.80):
        """
        Groups detected people by visual similarity.
        person_data: List of {'path': str, 'bbox': [x,y,x,y]}
        Returns: List of Lists of PIL Images (Groups)
        """
        embeddings = []
        crops = []
        
        # 1. Extract Embeddings
        for p in person_data:
            emb, crop = self.get_embedding(p['path'], p['bbox'])
            if emb is not None:
                embeddings.append(emb)
                crops.append(crop)
                
        if not embeddings: return []

        # 2. Compare Similarity
        matrix = cosine_similarity(np.array(embeddings))
        visited = [False] * len(embeddings)
        groups = []
        
        for i in range(len(embeddings)):
            if visited[i]: continue
            
            current_group = [crops[i]]
            visited[i] = True
            
            for j in range(i+1, len(embeddings)):
                if not visited[j] and matrix[i][j] > threshold:
                    current_group.append(crops[j])
                    visited[j] = True
            
            groups.append(current_group)
            
        return groups