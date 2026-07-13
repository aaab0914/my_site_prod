def sync_gallery_media():
    from my_site.media_sync import sync_site_media

    result = sync_site_media()
    gallery_result = result.get("gallery_sync", {})
    return {
        "missing_records": gallery_result.get("missing_records", 0),
        "created_records": gallery_result.get("created_records", 0),
        "missing_record_ids": gallery_result.get("missing_record_ids", []),
        "deleted_records": result.get("deleted_records", 0),
        "cleared_fields": result.get("cleared_fields", 0),
        "trashed_files": result.get("trashed_files", []),
        "missing_actions": result.get("missing_actions", []),
        "orphaned_files": result.get("orphaned_files", []),
    }
