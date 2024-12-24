from fastapi import APIRouter, HTTPException, Depends
from utils.auth import get_api_key, get_admin_key
from api.models import ProductIdea, Issue
from asgiref.sync import sync_to_async
from pydantic import BaseModel
from typing import Optional

# Define request body model
class ProductIdeaCreate(BaseModel):
    idea: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

class IssueCreate(BaseModel):
    description: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("/product-idea")
async def save_product_idea(
    idea_data: ProductIdeaCreate,
    api_key: str = Depends(get_api_key)
):
    try:
        @sync_to_async
        def create_idea():
            return ProductIdea.objects.create(
                idea=idea_data.idea,
                customer_email=idea_data.customer_email,
                customer_phone=idea_data.customer_phone
            )
        
        product_idea = await create_idea()
        
        return {
            "message": "Product idea saved successfully",
            "timestamp": product_idea.timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/issue")
async def save_issue(
    issue_data: IssueCreate,
    api_key: str = Depends(get_api_key)
):
    try:
        @sync_to_async
        def create_issue():
            return Issue.objects.create(
                description=issue_data.description,
                customer_email=issue_data.customer_email,
                customer_phone=issue_data.customer_phone
            )
        
        issue = await create_issue()
        
        return {
            "message": "Issue reported successfully",
            "timestamp": issue.timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/product-ideas")
async def list_product_ideas(
    admin_key: str = Depends(get_admin_key)
):
    try:
        @sync_to_async
        def get_ideas():
            return list(ProductIdea.objects.all().values())
        
        ideas = await get_ideas()
        return {"ideas": ideas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/issues")
async def list_issues(
    admin_key: str = Depends(get_admin_key)
):
    try:
        @sync_to_async
        def get_issues():
            return list(Issue.objects.all().values())
        
        issues = await get_issues()
        return {"issues": issues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 