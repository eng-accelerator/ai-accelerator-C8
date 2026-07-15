def reset_source_ingestion_rows(db: Session, *, source_id: int) -> dict[str, int]:
    image_ids = list(
        db.execute(
            select(SourceImage.image_id)
            .where(
                SourceImage.source_id == source_id,
                SourceImage.image_id.is_not(None),
            )
            .distinct()
        ).scalars()
    )

    deleted_source_images = int(
        db.execute(
            delete(SourceImage).where(SourceImage.source_id == source_id)
        ).rowcount
        or 0
    )

    deleted_checkpoints = 0

    orphaned_images = _orphaned_image_ids(db, candidate_ids=image_ids)

    if not orphaned_images:
        return {
            "deleted_source_images": deleted_source_images,
            "deleted_checkpoints": deleted_checkpoints,
            "deleted_t2i_samples": 0,
            "deleted_images": 0,
            "deleted_prompts": 0,
            "cleaned_file_storages": 0,
        }

    prompt_ids = list(
        db.execute(
            select(T2ISample.prompt_id).where(T2ISample.image_id.in_(orphaned_images))
        ).scalars()
    )

    deleted_t2i = int(
        db.execute(
            delete(T2ISample).where(T2ISample.image_id.in_(orphaned_images))
        ).rowcount
        or 0
    )

    deleted_prompts = _delete_orphan_prompts(db, prompt_ids=prompt_ids)

    canonical_file_ids = set(
        db.execute(
            select(Image.canonical_file_id).where(
                Image.id.in_(orphaned_images),
                Image.canonical_file_id.is_not(None),
            )
        ).scalars()
    )

    derivative_file_ids = set()

    if canonical_file_ids:
        derivative_file_ids = set(
            db.execute(
                select(File.id).where(
                    File.derivative_of_file_id.in_(canonical_file_ids)
                )
            ).scalars()
        )

    deleted_images = int(
        db.execute(
            delete(Image).where(Image.id.in_(orphaned_images))
        ).rowcount
        or 0
    )

    cleaned_storages = 0
    referenced_canonical_file_ids = set()

    if canonical_file_ids:
        referenced_canonical_file_ids = set(
            db.execute(
                select(Image.canonical_file_id)
                .where(Image.canonical_file_id.in_(canonical_file_ids))
                .distinct()
            ).scalars()
        )

    clean_file_ids = derivative_file_ids | (
        canonical_file_ids - referenced_canonical_file_ids
    )

    if clean_file_ids:
        cleaned_storages = int(
            db.execute(
                update(FileStorage)
                .where(FileStorage.file_id.in_(clean_file_ids))
                .values(status=model_constants.FILE_STORAGE_STATUS_CLEANED)
            ).rowcount
            or 0
        )

    return {
        "deleted_source_images": deleted_source_images,
        "deleted_checkpoints": deleted_checkpoints,
        "deleted_t2i_samples": deleted_t2i,
        "deleted_images": deleted_images,
        "deleted_prompts": deleted_prompts,
        "cleaned_file_storages": cleaned_storages,
    }
