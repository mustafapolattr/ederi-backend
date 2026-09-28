from django.urls import path

from .views import AnalyzeView, ChatView, ParseTransactionView, ScenarioView

urlpatterns = [
    path("parse-transaction/", ParseTransactionView.as_view(), name="ai-parse-transaction"),
    path("analyze/", AnalyzeView.as_view(), name="ai-analyze"),
    path("chat/", ChatView.as_view(), name="ai-chat"),
    path("scenario/", ScenarioView.as_view(), name="ai-scenario"),
]
