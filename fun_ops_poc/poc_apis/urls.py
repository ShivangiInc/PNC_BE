from django.urls import path
from .views import ExcelUploadView
from .views import ExcelDataView
from .views import (
    ModifyRecordView,
    AddColumnView,
    SoftDeleteColumnView,
    RenameColumnView,
    ExcelExportView,
    PdfExportView,
    DeletionApprovedView
)

urlpatterns = [
    path("upload/", ExcelUploadView.as_view(), name="excel-upload"),
    path("data/", ExcelDataView.as_view(), name="excel-data"),
    path("create_or_update_record/", ModifyRecordView.as_view(), name="create-record"),
    path(
        "create_or_update_record/<str:record_id>/",
        ModifyRecordView.as_view(),
        name="update-record",
    ),
    path("add-column/", AddColumnView.as_view(), name="add_column"),
    path(
        "soft-delete-column/", SoftDeleteColumnView.as_view(), name="soft_delete_column"
    ),
    path("rename-column/", RenameColumnView.as_view(), name="rename_column"),
    path('export/excel/', ExcelExportView.as_view(), name='export_excel'),
    path('export/pdf/', PdfExportView.as_view(), name='export_pdf'),
    path('deleted_by_admin/<str:record_id>/',DeletionApprovedView.as_view(), name="deleted_by_admin"),


]
