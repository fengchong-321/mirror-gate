"""清理重复的分组数据脚本。

此脚本用于清理 testcase_groups 表中的重复分组。
重复定义：相同 parent_id 和 name 的分组（忽略大小写和前后空格）。
保留策略：保留 ID 最小的分组，删除其他重复的。
"""

from app.database import SessionLocal
from app.models.testcase import TestCaseGroup, TestCase
from sqlalchemy import func


def clean_duplicate_groups():
    """清理重复的分组。"""
    db = SessionLocal()
    try:
        # 查找重复分组
        duplicates = (
            db.query(
                TestCaseGroup.parent_id,
                func.lower(func.trim(TestCaseGroup.name)).label("name_key"),
                func.count().label("cnt"),
                func.min(TestCaseGroup.id).label("min_id")
            )
            .group_by(TestCaseGroup.parent_id, func.lower(func.trim(TestCaseGroup.name)))
            .having(func.count() > 1)
            .all()
        )

        if not duplicates:
            print("✅ 没有发现重复分组")
            return

        print(f"发现 {len(duplicates)} 组重复分组")

        deleted_count = 0
        for dup in duplicates:
            parent_id, name_key, count, keep_id = dup

            # 找出要删除的分组（除了最小 ID 外的所有）
            to_delete = (
                db.query(TestCaseGroup)
                .filter(
                    TestCaseGroup.parent_id == parent_id,
                    func.lower(func.trim(TestCaseGroup.name)) == name_key,
                    TestCaseGroup.id != keep_id
                )
                .all()
            )

            print(f"\n分组名称：{name_key!r} (parent_id={parent_id})")
            print(f"  保留 ID: {keep_id}")
            for g in to_delete:
                print(f"  删除 ID: {g.id} (name={g.name!r})")

            # 先移动子分组到保留的分组下
            children = (
                db.query(TestCaseGroup)
                .filter(TestCaseGroup.parent_id.in_([g.id for g in to_delete]))
                .all()
            )
            for child in children:
                child.parent_id = keep_id
                print(f"  移动子分组 ID={child.id} 到 parent_id={keep_id}")

            # 移动用例到保留的分组下
            cases = (
                db.query(TestCase)
                .filter(TestCase.group_id.in_([g.id for g in to_delete]))
                .all()
            )
            for case in cases:
                case.group_id = keep_id
                print(f"  移动用例 ID={case.id} 到 group_id={keep_id}")

            # 删除重复分组
            for g in to_delete:
                db.delete(g)
                deleted_count += 1

        db.commit()
        print(f"\n✅ 清理完成！共删除 {deleted_count} 个重复分组")

    except Exception as e:
        db.rollback()
        print(f"❌ 清理失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("清理重复分组数据脚本")
    print("=" * 50)
    clean_duplicate_groups()
