# 用例管理模块实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现完整的用例管理模块，包括用例分组（目录树）、用例CRUD、附件、评论和变更历史功能。

**Architecture:** 采用分层架构，后端使用 FastAPI + SQLAlchemy，前端使用 Vue 3 + Element Plus。用例分组采用多级树形结构，用例挂载在目录节点下。

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Pydantic, Vue 3, Element Plus, TypeScript, MySQL 8.0

---

## Phase 1: 数据模型层

### Task 1: 用例分组模型 (TestCaseGroup)

**Files:**
- Create: `backend/app/models/testcase.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/test_testcase_models.py`

**Step 1: 创建测试文件**

```python
# backend/tests/test_testcase_models.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.testcase import TestCaseGroup, TestCase, CaseStatus


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_testcase_group(db_session):
    """测试创建用例分组"""
    group = TestCaseGroup(
        name="用户模块",
        parent_id=None,
        order=1,
        created_by="admin"
    )
    db_session.add(group)
    db_session.commit()

    assert group.id is not None
    assert group.name == "用户模块"
    assert group.order == 1


def test_create_nested_group(db_session):
    """测试创建嵌套分组"""
    parent = TestCaseGroup(name="用户模块", created_by="admin")
    db_session.add(parent)
    db_session.commit()

    child = TestCaseGroup(
        name="登录功能",
        parent_id=parent.id,
        created_by="admin"
    )
    db_session.add(child)
    db_session.commit()

    assert child.parent_id == parent.id


def test_create_testcase(db_session):
    """测试创建用例"""
    group = TestCaseGroup(name="测试分组", created_by="admin")
    db_session.add(group)
    db_session.commit()

    case = TestCase(
        group_id=group.id,
        title="用户登录测试",
        code="TC-20260302-001",
        created_by="admin"
    )
    db_session.add(case)
    db_session.commit()

    assert case.id is not None
    assert case.title == "用户登录测试"
    assert case.status == CaseStatus.DRAFT
```

**Step 2: 运行测试验证失败**

```bash
cd backend && pytest tests/test_testcase_models.py -v
```
Expected: FAIL with "cannot import name 'TestCaseGroup'"

**Step 3: 创建模型文件**

```python
# backend/app/models/testcase.py
"""用例管理模型

此模块定义用例管理相关的SQLAlchemy模型。
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class CaseType(str, enum.Enum):
    """用例类型"""
    FUNCTIONAL = "功能测试"
    PERFORMANCE = "性能测试"
    SECURITY = "安全测试"
    COMPATIBILITY = "兼容性测试"
    UX = "用户体验测试"
    OTHER = "其他"


class Platform(str, enum.Enum):
    """所属平台"""
    RN = "RN"          # Android + H5
    SERVER = "服务端"
    MINIAPP = "小程序"
    WEB = "Web"
    H5 = "H5"


class Priority(str, enum.Enum):
    """重要程度"""
    P0 = "P0"  # 最高
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"  # 最低


class CaseStatus(str, enum.Enum):
    """用例状态"""
    DRAFT = "草稿"
    REVIEWING = "评审中"
    PASSED = "通过"
    DEPRECATED = "废弃"


class TestCaseGroup(Base):
    """用例分组模型（目录树）"""
    __tablename__ = "testcase_groups"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(100), nullable=False)
    parent_id: Optional[int] = Column(Integer, ForeignKey("testcase_groups.id"), nullable=True, index=True)
    order: int = Column(Integer, default=0)
    created_by: Optional[str] = Column(String(50))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Column(String(50))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    children: List["TestCaseGroup"] = relationship(
        "TestCaseGroup",
        backref="parent",
        remote_side=[id],
        cascade="all, delete-orphan"
    )
    cases: List["TestCase"] = relationship(
        "TestCase",
        back_populates="group",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TestCaseGroup(id={self.id}, name={self.name!r})>"


class TestCase(Base):
    """测试用例模型"""
    __tablename__ = "testcases"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    group_id: int = Column(Integer, ForeignKey("testcase_groups.id"), nullable=False, index=True)
    code: str = Column(String(50), unique=True, nullable=False)  # 用例编号
    title: str = Column(String(200), nullable=False)
    order: int = Column(Integer, default=0)

    # 分类属性
    case_type: Optional[CaseType] = Column(Enum(CaseType), nullable=True)
    platform: Optional[Platform] = Column(Enum(Platform), nullable=True)
    priority: Optional[Priority] = Column(Enum(Priority), nullable=True)
    is_core: bool = Column(Boolean, default=False)

    # 人员信息
    owner: Optional[str] = Column(String(50))  # 维护人
    developer: Optional[str] = Column(String(50))  # 开发负责人

    # 测试内容
    page_url: Optional[str] = Column(String(500))
    preconditions: Optional[str] = Column(Text)  # 前置条件（富文本）
    steps: Optional[str] = Column(JSON)  # 测试步骤 [{"step": "...", "expected": "..."}]
    remark: Optional[str] = Column(Text)  # 备注（富文本）
    tags: Optional[str] = Column(JSON)  # 标签数组

    # 状态
    status: CaseStatus = Column(Enum(CaseStatus), default=CaseStatus.DRAFT)

    # 时间戳
    created_by: Optional[str] = Column(String(50))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Column(String(50))
    updated_at: datetime = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    group: Optional["TestCaseGroup"] = relationship("TestCaseGroup", back_populates="cases")
    attachments: List["TestCaseAttachment"] = relationship(
        "TestCaseAttachment",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    comments: List["TestCaseComment"] = relationship(
        "TestCaseComment",
        back_populates="case",
        cascade="all, delete-orphan"
    )
    history: List["TestCaseHistory"] = relationship(
        "TestCaseHistory",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TestCase(id={self.id}, code={self.code!r}, title={self.title!r})>"


class TestCaseAttachment(Base):
    """用例附件模型"""
    __tablename__ = "testcase_attachments"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    case_id: int = Column(Integer, ForeignKey("testcases.id"), nullable=False, index=True)
    filename: str = Column(String(255), nullable=False)
    file_path: str = Column(String(500), nullable=False)
    file_size: int = Column(Integer, default=0)
    file_type: Optional[str] = Column(String(100))
    uploaded_by: Optional[str] = Column(String(50))
    uploaded_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    case: Optional["TestCase"] = relationship("TestCase", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<TestCaseAttachment(id={self.id}, filename={self.filename!r})>"


class TestCaseComment(Base):
    """用例评论模型"""
    __tablename__ = "testcase_comments"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    case_id: int = Column(Integer, ForeignKey("testcases.id"), nullable=False, index=True)
    parent_id: Optional[int] = Column(Integer, ForeignKey("testcase_comments.id"), nullable=True)
    content: str = Column(Text, nullable=False)
    created_by: Optional[str] = Column(String(50))
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    case: Optional["TestCase"] = relationship("TestCase", back_populates="comments")
    replies: List["TestCaseComment"] = relationship(
        "TestCaseComment",
        backref="parent_comment",
        remote_side=[id]
    )

    def __repr__(self) -> str:
        return f"<TestCaseComment(id={self.id}, case_id={self.case_id})>"


class TestCaseHistory(Base):
    """用例变更历史模型"""
    __tablename__ = "testcase_history"
    __allow_unmapped__ = True

    id: int = Column(Integer, primary_key=True, index=True)
    case_id: int = Column(Integer, ForeignKey("testcases.id"), nullable=False, index=True)
    field_name: str = Column(String(100), nullable=False)  # 修改的字段名
    old_value: Optional[str] = Column(Text)  # 旧值
    new_value: Optional[str] = Column(Text)  # 新值
    changed_by: Optional[str] = Column(String(50))
    changed_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    case: Optional["TestCase"] = relationship("TestCase", back_populates="history")

    def __repr__(self) -> str:
        return f"<TestCaseHistory(id={self.id}, field={self.field_name!r})>"
```

**Step 4: 更新 __init__.py 导出**

```python
# 添加到 backend/app/models/__init__.py

from app.models.testcase import (
    TestCaseGroup,
    TestCase,
    TestCaseAttachment,
    TestCaseComment,
    TestCaseHistory,
    CaseType,
    Platform,
    Priority,
    CaseStatus,
)

# 添加到 __all__ 列表
    # Testcase models
    "TestCaseGroup",
    "TestCase",
    "TestCaseAttachment",
    "TestCaseComment",
    "TestCaseHistory",
    "CaseType",
    "Platform",
    "Priority",
    "CaseStatus",
```

**Step 5: 运行测试验证通过**

```bash
cd backend && pytest tests/test_testcase_models.py -v
```
Expected: PASS

**Step 6: 提交**

```bash
git add backend/app/models/testcase.py backend/app/models/__init__.py backend/tests/test_testcase_models.py
git commit -m "feat(testcase): add testcase models (group, case, attachment, comment, history)"
```

---

### Task 2: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/testcase.py`

**Step 1: 创建 Schemas**

```python
# backend/app/schemas/testcase.py
"""用例管理 Pydantic Schemas

此模块定义用例管理相关的请求/响应模式。
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from app.models.testcase import CaseType, Platform, Priority, CaseStatus


# ============ TestStep ============
class TestStep(BaseModel):
    """测试步骤"""
    step: str = Field(..., description="步骤描述")
    expected: str = Field(..., description="预期结果")


# ============ TestCaseGroup Schemas ============
class TestCaseGroupBase(BaseModel):
    """用例分组基础模式"""
    name: str = Field(..., max_length=100, description="分组名称")
    parent_id: Optional[int] = Field(None, description="父分组ID")
    order: int = Field(0, description="排序序号")


class TestCaseGroupCreate(TestCaseGroupBase):
    """创建用例分组"""
    pass


class TestCaseGroupUpdate(BaseModel):
    """更新用例分组"""
    name: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[int] = None
    order: Optional[int] = None


class TestCaseGroupResponse(TestCaseGroupBase):
    """用例分组响应"""
    id: int
    created_by: Optional[str]
    created_at: datetime
    updated_by: Optional[str]
    updated_at: datetime
    children: List["TestCaseGroupResponse"] = []
    case_count: int = 0

    class Config:
        from_attributes = True


# ============ TestCase Schemas ============
class TestCaseBase(BaseModel):
    """用例基础模式"""
    title: str = Field(..., max_length=200, description="用例标题")
    case_type: Optional[CaseType] = Field(None, description="用例类型")
    platform: Optional[Platform] = Field(None, description="所属平台")
    priority: Optional[Priority] = Field(None, description="重要程度")
    is_core: bool = Field(False, description="是否核心用例")
    owner: Optional[str] = Field(None, max_length=50, description="维护人")
    developer: Optional[str] = Field(None, max_length=50, description="开发负责人")
    page_url: Optional[str] = Field(None, max_length=500, description="页面地址")
    preconditions: Optional[str] = Field(None, description="前置条件")
    steps: Optional[List[TestStep]] = Field(None, description="测试步骤")
    remark: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签")
    status: CaseStatus = Field(CaseStatus.DRAFT, description="状态")


class TestCaseCreate(TestCaseBase):
    """创建用例"""
    group_id: int = Field(..., description="所属分组ID")


class TestCaseUpdate(BaseModel):
    """更新用例"""
    group_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=200)
    case_type: Optional[CaseType] = None
    platform: Optional[Platform] = None
    priority: Optional[Priority] = None
    is_core: Optional[bool] = None
    owner: Optional[str] = Field(None, max_length=50)
    developer: Optional[str] = Field(None, max_length=50)
    page_url: Optional[str] = Field(None, max_length=500)
    preconditions: Optional[str] = None
    steps: Optional[List[TestStep]] = None
    remark: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[CaseStatus] = None


class TestCaseResponse(TestCaseBase):
    """用例响应"""
    id: int
    group_id: int
    code: str
    order: int
    created_by: Optional[str]
    created_at: datetime
    updated_by: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


class TestCaseListResponse(BaseModel):
    """用例列表响应"""
    total: int
    items: List[TestCaseResponse]


class TestCaseDetailResponse(TestCaseResponse):
    """用例详情响应（包含附件、评论、历史）"""
    attachments: List["TestCaseAttachmentResponse"] = []
    comments: List["TestCaseCommentResponse"] = []
    history: List["TestCaseHistoryResponse"] = []


# ============ TestCaseAttachment Schemas ============
class TestCaseAttachmentResponse(BaseModel):
    """附件响应"""
    id: int
    case_id: int
    filename: str
    file_path: str
    file_size: int
    file_type: Optional[str]
    uploaded_by: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ============ TestCaseComment Schemas ============
class TestCaseCommentBase(BaseModel):
    """评论基础模式"""
    content: str = Field(..., description="评论内容")


class TestCaseCommentCreate(TestCaseCommentBase):
    """创建评论"""
    parent_id: Optional[int] = Field(None, description="父评论ID")


class TestCaseCommentResponse(TestCaseCommentBase):
    """评论响应"""
    id: int
    case_id: int
    parent_id: Optional[int]
    created_by: Optional[str]
    created_at: datetime
    replies: List["TestCaseCommentResponse"] = []

    class Config:
        from_attributes = True


# ============ TestCaseHistory Schemas ============
class TestCaseHistoryResponse(BaseModel):
    """变更历史响应"""
    id: int
    case_id: int
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_by: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True


# ============ Tree Node ============
class TreeNode(BaseModel):
    """树节点（用于目录树展示）"""
    id: int
    label: str
    parent_id: Optional[int]
    order: int
    case_count: int = 0
    children: List["TreeNode"] = []


# 更新 forward references
TestCaseGroupResponse.model_rebuild()
TestCaseDetailResponse.model_rebuild()
TestCaseCommentResponse.model_rebuild()
TreeNode.model_rebuild()
```

**Step 2: 提交**

```bash
git add backend/app/schemas/testcase.py
git commit -m "feat(testcase): add pydantic schemas"
```

---

## Phase 2: 服务层

### Task 3: 用例分组服务

**Files:**
- Create: `backend/app/services/testcase_service.py`
- Test: `backend/tests/test_testcase_service.py`

**Step 1: 创建服务测试**

```python
# backend/tests/test_testcase_service.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.testcase_service import TestCaseService
from app.schemas.testcase import TestCaseGroupCreate, TestCaseCreate


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def service(db_session):
    return TestCaseService(db_session)


def test_create_group(service):
    """测试创建分组"""
    group_data = TestCaseGroupCreate(name="用户模块")
    group = service.create_group(group_data, created_by="admin")

    assert group.id is not None
    assert group.name == "用户模块"
    assert group.created_by == "admin"


def test_create_nested_group(service):
    """测试创建嵌套分组"""
    parent = service.create_group(
        TestCaseGroupCreate(name="用户模块"),
        created_by="admin"
    )

    child = service.create_group(
        TestCaseGroupCreate(name="登录功能", parent_id=parent.id),
        created_by="admin"
    )

    assert child.parent_id == parent.id


def test_get_group_tree(service):
    """测试获取分组树"""
    # 创建层级结构
    parent = service.create_group(
        TestCaseGroupCreate(name="用户模块", order=1),
        created_by="admin"
    )
    child1 = service.create_group(
        TestCaseGroupCreate(name="登录", parent_id=parent.id, order=1),
        created_by="admin"
    )
    child2 = service.create_group(
        TestCaseGroupCreate(name="注册", parent_id=parent.id, order=2),
        created_by="admin"
    )

    tree = service.get_group_tree()
    assert len(tree) == 1
    assert tree[0].label == "用户模块"
    assert len(tree[0].children) == 2


def test_create_testcase(service):
    """测试创建用例"""
    group = service.create_group(
        TestCaseGroupCreate(name="测试分组"),
        created_by="admin"
    )

    case_data = TestCaseCreate(
        group_id=group.id,
        title="用户登录测试"
    )
    case = service.create_case(case_data, created_by="admin")

    assert case.id is not None
    assert case.title == "用户登录测试"
    assert case.code.startswith("TC-")


def test_generate_case_code(service):
    """测试用例编号生成"""
    code1 = service._generate_case_code()
    code2 = service._generate_case_code()

    assert code1.startswith("TC-")
    assert code1 != code2  # 编号应该唯一
```

**Step 2: 运行测试验证失败**

```bash
cd backend && pytest tests/test_testcase_service.py -v
```
Expected: FAIL

**Step 3: 创建服务文件**

```python
# backend/app/services/testcase_service.py
"""用例管理服务

此模块实现用例管理的业务逻辑。
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
import json

from app.models.testcase import (
    TestCaseGroup,
    TestCase,
    TestCaseAttachment,
    TestCaseComment,
    TestCaseHistory,
    CaseStatus,
)
from app.schemas.testcase import (
    TestCaseGroupCreate,
    TestCaseGroupUpdate,
    TestCaseGroupResponse,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestCaseDetailResponse,
    TestCaseAttachmentResponse,
    TestCaseCommentCreate,
    TestCaseCommentResponse,
    TestCaseHistoryResponse,
    TreeNode,
)


class TestCaseService:
    def __init__(self, db: Session):
        self.db = db

    # ============ 用例分组 ============
    def create_group(
        self,
        group_data: TestCaseGroupCreate,
        created_by: str
    ) -> TestCaseGroup:
        """创建用例分组"""
        group = TestCaseGroup(
            name=group_data.name,
            parent_id=group_data.parent_id,
            order=group_data.order,
            created_by=created_by
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group

    def get_group(self, group_id: int) -> Optional[TestCaseGroup]:
        """获取单个分组"""
        return self.db.query(TestCaseGroup).filter(
            TestCaseGroup.id == group_id
        ).first()

    def get_group_tree(self) -> List[TreeNode]:
        """获取分组树"""
        # 获取所有分组
        groups = self.db.query(TestCaseGroup).order_by(TestCaseGroup.order).all()

        # 获取每个分组的用例数量
        case_counts = self.db.query(
            TestCase.group_id,
            func.count(TestCase.id).label('count')
        ).group_by(TestCase.group_id).all()
        count_dict = {c.group_id: c.count for c in case_counts}

        # 构建树
        group_map = {}
        root_nodes = []

        for group in groups:
            node = TreeNode(
                id=group.id,
                label=group.name,
                parent_id=group.parent_id,
                order=group.order,
                case_count=count_dict.get(group.id, 0),
                children=[]
            )
            group_map[group.id] = node

        for group in groups:
            node = group_map[group.id]
            if group.parent_id is None:
                root_nodes.append(node)
            elif group.parent_id in group_map:
                group_map[group.parent_id].children.append(node)

        return root_nodes

    def update_group(
        self,
        group_id: int,
        group_data: TestCaseGroupUpdate,
        updated_by: str
    ) -> TestCaseGroup:
        """更新分组"""
        group = self.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="分组不存在")

        update_data = group_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(group, key, value)

        group.updated_by = updated_by
        self.db.commit()
        self.db.refresh(group)
        return group

    def delete_group(self, group_id: int) -> bool:
        """删除分组（级联删除子分组和用例）"""
        group = self.get_group(group_id)
        if not group:
            raise HTTPException(status_code=404, detail="分组不存在")

        self.db.delete(group)
        self.db.commit()
        return True

    # ============ 用例 ============
    def _generate_case_code(self) -> str:
        """生成用例编号 TC-YYYYMMDD-NNN"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"TC-{today}-"

        # 查找今天已有的最大编号
        last_case = self.db.query(TestCase).filter(
            TestCase.code.like(f"{prefix}%")
        ).order_by(TestCase.code.desc()).first()

        if last_case:
            last_num = int(last_case.code.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:03d}"

    def create_case(
        self,
        case_data: TestCaseCreate,
        created_by: str
    ) -> TestCase:
        """创建用例"""
        # 检查分组是否存在
        group = self.get_group(case_data.group_id)
        if not group:
            raise HTTPException(status_code=400, detail="分组不存在")

        case = TestCase(
            group_id=case_data.group_id,
            code=self._generate_case_code(),
            title=case_data.title,
            case_type=case_data.case_type,
            platform=case_data.platform,
            priority=case_data.priority,
            is_core=case_data.is_core,
            owner=case_data.owner,
            developer=case_data.developer,
            page_url=case_data.page_url,
            preconditions=case_data.preconditions,
            steps=[s.model_dump() for s in case_data.steps] if case_data.steps else None,
            remark=case_data.remark,
            tags=case_data.tags,
            status=case_data.status,
            created_by=created_by
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def get_case(self, case_id: int) -> Optional[TestCase]:
        """获取单个用例"""
        return self.db.query(TestCase).filter(TestCase.id == case_id).first()

    def get_case_detail(self, case_id: int) -> Optional[TestCaseDetailResponse]:
        """获取用例详情（包含附件、评论、历史）"""
        case = self.get_case(case_id)
        if not case:
            return None

        return TestCaseDetailResponse(
            id=case.id,
            group_id=case.group_id,
            code=case.code,
            title=case.title,
            order=case.order,
            case_type=case.case_type,
            platform=case.platform,
            priority=case.priority,
            is_core=case.is_core,
            owner=case.owner,
            developer=case.developer,
            page_url=case.page_url,
            preconditions=case.preconditions,
            steps=case.steps,
            remark=case.remark,
            tags=case.tags,
            status=case.status,
            created_by=case.created_by,
            created_at=case.created_at,
            updated_by=case.updated_by,
            updated_at=case.updated_at,
            attachments=[
                TestCaseAttachmentResponse.model_validate(a)
                for a in case.attachments
            ],
            comments=[
                self._build_comment_tree(c)
                for c in case.comments if c.parent_id is None
            ],
            history=[
                TestCaseHistoryResponse.model_validate(h)
                for h in case.history
            ]
        )

    def _build_comment_tree(self, comment: TestCaseComment) -> TestCaseCommentResponse:
        """构建评论树"""
        return TestCaseCommentResponse(
            id=comment.id,
            case_id=comment.case_id,
            parent_id=comment.parent_id,
            content=comment.content,
            created_by=comment.created_by,
            created_at=comment.created_at,
            replies=[
                self._build_comment_tree(r) for r in comment.replies
            ]
        )

    def get_cases_by_group(
        self,
        group_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[TestCase]:
        """获取分组下的用例列表"""
        return self.db.query(TestCase).filter(
            TestCase.group_id == group_id
        ).order_by(TestCase.order).offset(skip).limit(limit).all()

    def count_cases_by_group(self, group_id: int) -> int:
        """统计分组下的用例数量"""
        return self.db.query(TestCase).filter(
            TestCase.group_id == group_id
        ).count()

    def update_case(
        self,
        case_id: int,
        case_data: TestCaseUpdate,
        updated_by: str
    ) -> TestCase:
        """更新用例"""
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="用例不存在")

        update_data = case_data.model_dump(exclude_unset=True)

        # 记录变更历史
        for key, new_value in update_data.items():
            if key == "steps":
                old_value = case.steps
                new_value = [s.model_dump() for s in new_value] if new_value else None
            elif key == "tags":
                old_value = case.tags
            else:
                old_value = getattr(case, key, None)

            if old_value != new_value:
                self._record_history(
                    case_id,
                    key,
                    str(old_value) if old_value else None,
                    str(new_value) if new_value else None,
                    updated_by
                )

        # 应用更新
        for key, value in update_data.items():
            if key == "steps" and value:
                value = [s.model_dump() for s in value]
            setattr(case, key, value)

        case.updated_by = updated_by
        self.db.commit()
        self.db.refresh(case)
        return case

    def _record_history(
        self,
        case_id: int,
        field_name: str,
        old_value: Optional[str],
        new_value: Optional[str],
        changed_by: str
    ):
        """记录变更历史"""
        history = TestCaseHistory(
            case_id=case_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by
        )
        self.db.add(history)

    def delete_case(self, case_id: int) -> bool:
        """删除用例"""
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="用例不存在")

        self.db.delete(case)
        self.db.commit()
        return True

    def copy_case(self, case_id: int, created_by: str) -> TestCase:
        """复制用例"""
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="用例不存在")

        new_case = TestCase(
            group_id=case.group_id,
            code=self._generate_case_code(),
            title=f"{case.title} (副本)",
            case_type=case.case_type,
            platform=case.platform,
            priority=case.priority,
            is_core=case.is_core,
            owner=case.owner,
            developer=case.developer,
            page_url=case.page_url,
            preconditions=case.preconditions,
            steps=case.steps,
            remark=case.remark,
            tags=case.tags,
            status=CaseStatus.DRAFT,
            created_by=created_by
        )
        self.db.add(new_case)
        self.db.commit()
        self.db.refresh(new_case)
        return new_case

    def move_case(self, case_id: int, new_group_id: int, updated_by: str) -> TestCase:
        """移动用例到其他分组"""
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="用例不存在")

        new_group = self.get_group(new_group_id)
        if not new_group:
            raise HTTPException(status_code=400, detail="目标分组不存在")

        self._record_history(
            case_id,
            "group_id",
            str(case.group_id),
            str(new_group_id),
            updated_by
        )

        case.group_id = new_group_id
        case.updated_by = updated_by
        self.db.commit()
        self.db.refresh(case)
        return case

    def reorder_cases(self, group_id: int, case_orders: List[dict]) -> bool:
        """批量更新用例排序"""
        for item in case_orders:
            case = self.get_case(item["id"])
            if case and case.group_id == group_id:
                case.order = item["order"]

        self.db.commit()
        return True

    # ============ 评论 ============
    def add_comment(
        self,
        case_id: int,
        comment_data: TestCaseCommentCreate,
        created_by: str
    ) -> TestCaseComment:
        """添加评论"""
        case = self.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="用例不存在")

        comment = TestCaseComment(
            case_id=case_id,
            parent_id=comment_data.parent_id,
            content=comment_data.content,
            created_by=created_by
        )
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def delete_comment(self, comment_id: int) -> bool:
        """删除评论"""
        comment = self.db.query(TestCaseComment).filter(
            TestCaseComment.id == comment_id
        ).first()

        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        self.db.delete(comment)
        self.db.commit()
        return True
```

**Step 4: 运行测试验证通过**

```bash
cd backend && pytest tests/test_testcase_service.py -v
```
Expected: PASS

**Step 5: 提交**

```bash
git add backend/app/services/testcase_service.py backend/tests/test_testcase_service.py
git commit -m "feat(testcase): add testcase service layer"
```

---

## Phase 3: API 层

### Task 4: API 路由

**Files:**
- Create: `backend/app/api/v1/testcase.py`
- Modify: `backend/app/main.py`

**Step 1: 创建 API 路由**

```python
# backend/app/api/v1/testcase.py
"""用例管理 API 路由

此模块定义用例管理相关的 REST API。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
import os
import uuid

from app.database import get_db
from app.services.testcase_service import TestCaseService
from app.schemas.testcase import (
    TestCaseGroupCreate,
    TestCaseGroupUpdate,
    TestCaseGroupResponse,
    TestCaseCreate,
    TestCaseUpdate,
    TestCaseResponse,
    TestCaseDetailResponse,
    TestCaseListResponse,
    TestCaseCommentCreate,
    TestCaseCommentResponse,
    TreeNode,
)


router = APIRouter(prefix="/testcase", tags=["用例管理"])


# ============ 用例分组 API ============
@router.post("/groups", response_model=TestCaseGroupResponse)
def create_group(
    group_data: TestCaseGroupCreate,
    db: Session = Depends(get_db)
):
    """创建用例分组"""
    service = TestCaseService(db)
    group = service.create_group(group_data, created_by="system")
    return TestCaseGroupResponse(
        id=group.id,
        name=group.name,
        parent_id=group.parent_id,
        order=group.order,
        created_by=group.created_by,
        created_at=group.created_at,
        updated_by=group.updated_by,
        updated_at=group.updated_at,
        children=[],
        case_count=0
    )


@router.get("/groups/tree", response_model=List[TreeNode])
def get_group_tree(db: Session = Depends(get_db)):
    """获取用例分组树"""
    service = TestCaseService(db)
    return service.get_group_tree()


@router.get("/groups/{group_id}", response_model=TestCaseGroupResponse)
def get_group(group_id: int, db: Session = Depends(get_db)):
    """获取单个分组"""
    service = TestCaseService(db)
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return TestCaseGroupResponse(
        id=group.id,
        name=group.name,
        parent_id=group.parent_id,
        order=group.order,
        created_by=group.created_by,
        created_at=group.created_at,
        updated_by=group.updated_by,
        updated_at=group.updated_at,
        children=[],
        case_count=service.count_cases_by_group(group_id)
    )


@router.put("/groups/{group_id}", response_model=TestCaseGroupResponse)
def update_group(
    group_id: int,
    group_data: TestCaseGroupUpdate,
    db: Session = Depends(get_db)
):
    """更新分组"""
    service = TestCaseService(db)
    group = service.update_group(group_id, group_data, updated_by="system")
    return TestCaseGroupResponse(
        id=group.id,
        name=group.name,
        parent_id=group.parent_id,
        order=group.order,
        created_by=group.created_by,
        created_at=group.created_at,
        updated_by=group.updated_by,
        updated_at=group.updated_at,
        children=[],
        case_count=service.count_cases_by_group(group_id)
    )


@router.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    """删除分组"""
    service = TestCaseService(db)
    service.delete_group(group_id)
    return {"message": "删除成功"}


# ============ 用例 API ============
@router.post("/cases", response_model=TestCaseResponse)
def create_case(
    case_data: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """创建用例"""
    service = TestCaseService(db)
    return service.create_case(case_data, created_by="system")


@router.get("/cases", response_model=TestCaseListResponse)
def list_cases(
    group_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """获取用例列表"""
    service = TestCaseService(db)
    cases = service.get_cases_by_group(group_id, skip, limit)
    total = service.count_cases_by_group(group_id)
    return TestCaseListResponse(total=total, items=cases)


@router.get("/cases/{case_id}", response_model=TestCaseDetailResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    """获取用例详情"""
    service = TestCaseService(db)
    case = service.get_case_detail(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    return case


@router.put("/cases/{case_id}", response_model=TestCaseResponse)
def update_case(
    case_id: int,
    case_data: TestCaseUpdate,
    db: Session = Depends(get_db)
):
    """更新用例"""
    service = TestCaseService(db)
    return service.update_case(case_id, case_data, updated_by="system")


@router.delete("/cases/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    """删除用例"""
    service = TestCaseService(db)
    service.delete_case(case_id)
    return {"message": "删除成功"}


@router.post("/cases/{case_id}/copy", response_model=TestCaseResponse)
def copy_case(case_id: int, db: Session = Depends(get_db)):
    """复制用例"""
    service = TestCaseService(db)
    return service.copy_case(case_id, created_by="system")


@router.post("/cases/{case_id}/move")
def move_case(
    case_id: int,
    new_group_id: int = Query(..., description="目标分组ID"),
    db: Session = Depends(get_db)
):
    """移动用例"""
    service = TestCaseService(db)
    return service.move_case(case_id, new_group_id, updated_by="system")


@router.put("/cases/reorder")
def reorder_cases(
    group_id: int,
    case_orders: List[dict],
    db: Session = Depends(get_db)
):
    """批量更新用例排序"""
    service = TestCaseService(db)
    service.reorder_cases(group_id, case_orders)
    return {"message": "排序更新成功"}


# ============ 评论 API ============
@router.get("/cases/{case_id}/comments", response_model=List[TestCaseCommentResponse])
def get_comments(case_id: int, db: Session = Depends(get_db)):
    """获取用例评论"""
    service = TestCaseService(db)
    case = service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    return [
        service._build_comment_tree(c)
        for c in case.comments if c.parent_id is None
    ]


@router.post("/cases/{case_id}/comments", response_model=TestCaseCommentResponse)
def add_comment(
    case_id: int,
    comment_data: TestCaseCommentCreate,
    db: Session = Depends(get_db)
):
    """添加评论"""
    service = TestCaseService(db)
    return service.add_comment(case_id, comment_data, created_by="system")


@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db)):
    """删除评论"""
    service = TestCaseService(db)
    service.delete_comment(comment_id)
    return {"message": "删除成功"}
```

**Step 2: 注册路由到 main.py**

```python
# 在 backend/app/main.py 添加
from app.api.v1 import testcase

app.include_router(testcase.router, prefix="/api/v1")
```

**Step 3: 提交**

```bash
git add backend/app/api/v1/testcase.py backend/app/main.py
git commit -m "feat(testcase): add testcase API routes"
```

---

## Phase 4: 数据库迁移

### Task 5: 创建数据库迁移

**Files:**
- Create: `backend/alembic/versions/002_testcase_tables.py`

**Step 1: 创建迁移文件**

```bash
cd backend && alembic revision -m "add testcase tables"
```

**Step 2: 编辑迁移文件**

```python
# backend/alembic/versions/002_testcase_tables.py
"""add testcase tables

Revision ID: 002
Revises:
Create Date: 2026-03-02

"""
from alembic import op
import sqlalchemy as sa
from app.models.testcase import CaseType, Platform, Priority, CaseStatus

# revision identifiers
revision = '002'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 用例分组表
    op.create_table(
        'testcase_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('created_by', sa.String(50)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_by', sa.String(50)),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['testcase_groups.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_testcase_groups_parent_id', 'testcase_groups', ['parent_id'])

    # 用例表
    op.create_table(
        'testcases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('case_type', sa.Enum(CaseType)),
        sa.Column('platform', sa.Enum(Platform)),
        sa.Column('priority', sa.Enum(Priority)),
        sa.Column('is_core', sa.Boolean(), default=False),
        sa.Column('owner', sa.String(50)),
        sa.Column('developer', sa.String(50)),
        sa.Column('page_url', sa.String(500)),
        sa.Column('preconditions', sa.Text()),
        sa.Column('steps', sa.JSON()),
        sa.Column('remark', sa.Text()),
        sa.Column('tags', sa.JSON()),
        sa.Column('status', sa.Enum(CaseStatus), default=CaseStatus.DRAFT),
        sa.Column('created_by', sa.String(50)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_by', sa.String(50)),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['group_id'], ['testcase_groups.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_testcases_group_id', 'testcases', ['group_id'])

    # 附件表
    op.create_table(
        'testcase_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), default=0),
        sa.Column('file_type', sa.String(100)),
        sa.Column('uploaded_by', sa.String(50)),
        sa.Column('uploaded_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['case_id'], ['testcases.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_testcase_attachments_case_id', 'testcase_attachments', ['case_id'])

    # 评论表
    op.create_table(
        'testcase_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by', sa.String(50)),
        sa.Column('created_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['case_id'], ['testcases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['testcase_comments.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_testcase_comments_case_id', 'testcase_comments', ['case_id'])

    # 变更历史表
    op.create_table(
        'testcase_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('old_value', sa.Text()),
        sa.Column('new_value', sa.Text()),
        sa.Column('changed_by', sa.String(50)),
        sa.Column('changed_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['case_id'], ['testcases.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_testcase_history_case_id', 'testcase_history', ['case_id'])


def downgrade():
    op.drop_table('testcase_history')
    op.drop_table('testcase_comments')
    op.drop_table('testcase_attachments')
    op.drop_table('testcases')
    op.drop_table('testcase_groups')
```

**Step 3: 运行迁移**

```bash
cd backend && alembic upgrade head
```

**Step 4: 提交**

```bash
git add backend/alembic/versions/
git commit -m "feat(testcase): add database migration for testcase tables"
```

---

## Phase 5: 前端实现

### Task 6: API 客户端

**Files:**
- Create: `frontend/src/api/testcase.ts`

**Step 1: 创建 API 客户端**

```typescript
// frontend/src/api/testcase.ts
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

// 类型定义
export interface TreeNode {
  id: number
  label: string
  parent_id: number | null
  order: number
  case_count: number
  children: TreeNode[]
}

export interface TestCaseGroup {
  id: number
  name: string
  parent_id: number | null
  order: number
  created_by: string
  created_at: string
  updated_by: string
  updated_at: string
  case_count: number
}

export interface TestStep {
  step: string
  expected: string
}

export interface TestCase {
  id: number
  group_id: number
  code: string
  title: string
  order: number
  case_type?: string
  platform?: string
  priority?: string
  is_core: boolean
  owner?: string
  developer?: string
  page_url?: string
  preconditions?: string
  steps?: TestStep[]
  remark?: string
  tags?: string[]
  status: string
  created_by: string
  created_at: string
  updated_by: string
  updated_at: string
}

export interface TestCaseDetail extends TestCase {
  attachments: TestCaseAttachment[]
  comments: TestCaseComment[]
  history: TestCaseHistory[]
}

export interface TestCaseAttachment {
  id: number
  case_id: number
  filename: string
  file_path: string
  file_size: number
  file_type: string
  uploaded_by: string
  uploaded_at: string
}

export interface TestCaseComment {
  id: number
  case_id: number
  parent_id: number | null
  content: string
  created_by: string
  created_at: string
  replies: TestCaseComment[]
}

export interface TestCaseHistory {
  id: number
  case_id: number
  field_name: string
  old_value: string | null
  new_value: string | null
  changed_by: string
  changed_at: string
}

// API 方法
export const testcaseApi = {
  // 分组
  getGroupTree: () => api.get<TreeNode[]>('/testcase/groups/tree'),
  createGroup: (data: Partial<TestCaseGroup>) => api.post<TestCaseGroup>('/testcase/groups', data),
  updateGroup: (id: number, data: Partial<TestCaseGroup>) => api.put<TestCaseGroup>(`/testcase/groups/${id}`, data),
  deleteGroup: (id: number) => api.delete(`/testcase/groups/${id}`),

  // 用例
  getCases: (groupId: number, skip = 0, limit = 100) =>
    api.get<{ total: number; items: TestCase[] }>('/testcase/cases', { params: { group_id: groupId, skip, limit } }),
  getCase: (id: number) => api.get<TestCaseDetail>(`/testcase/cases/${id}`),
  createCase: (data: Partial<TestCase>) => api.post<TestCase>('/testcase/cases', data),
  updateCase: (id: number, data: Partial<TestCase>) => api.put<TestCase>(`/testcase/cases/${id}`, data),
  deleteCase: (id: number) => api.delete(`/testcase/cases/${id}`),
  copyCase: (id: number) => api.post<TestCase>(`/testcase/cases/${id}/copy`),
  moveCase: (id: number, newGroupId: number) =>
    api.post(`/testcase/cases/${id}/move`, null, { params: { new_group_id: newGroupId } }),

  // 评论
  getComments: (caseId: number) => api.get<TestCaseComment[]>(`/testcase/cases/${caseId}/comments`),
  addComment: (caseId: number, data: { content: string; parent_id?: number }) =>
    api.post<TestCaseComment>(`/testcase/cases/${caseId}/comments`, data),
  deleteComment: (id: number) => api.delete(`/testcase/comments/${id}`),
}
```

**Step 2: 提交**

```bash
git add frontend/src/api/testcase.ts
git commit -m "feat(testcase): add frontend API client"
```

---

### Task 7: 用例管理主页面

**Files:**
- Create: `frontend/src/views/testcase/index.vue`
- Modify: `frontend/src/router/index.ts`

**Step 1: 创建主页面**

```vue
<!-- frontend/src/views/testcase/index.vue -->
<template>
  <div class="testcase-container">
    <!-- 左侧目录树 -->
    <div class="left-panel">
      <el-card>
        <template #header>
          <div class="panel-header">
            <span>用例分组</span>
            <el-button type="primary" size="small" @click="handleAddGroup">
              新增
            </el-button>
          </div>
        </template>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索分组"
          clearable
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-tree
          ref="treeRef"
          :data="groupTree"
          :props="{ label: 'label', children: 'children' }"
          node-key="id"
          highlight-current
          default-expand-all
          @node-click="handleNodeClick"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <span>{{ data.label }}</span>
              <span class="case-count">({{ data.case_count }})</span>
              <div class="node-actions">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click.stop="handleAddSubGroup(data)"
                >
                  添加子分组
                </el-button>
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click.stop="handleEditGroup(data)"
                >
                  编辑
                </el-button>
                <el-button
                  type="danger"
                  link
                  size="small"
                  @click.stop="handleDeleteGroup(data)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </template>
        </el-tree>
      </el-card>
    </div>

    <!-- 右侧用例列表 -->
    <div class="right-panel">
      <el-card v-if="selectedGroup">
        <template #header>
          <div class="panel-header">
            <span>{{ selectedGroup.label }} - 用例列表</span>
            <div class="header-actions">
              <el-button type="primary" @click="handleAddCase">
                新建用例
              </el-button>
              <el-dropdown>
                <el-button>
                  列设置 <el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-checkbox-group v-model="visibleColumns">
                      <el-dropdown-item v-for="col in allColumns" :key="col.prop">
                        <el-checkbox :label="col.prop">{{ col.label }}</el-checkbox>
                      </el-dropdown-item>
                    </el-checkbox-group>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </template>

        <el-table :data="caseList" v-loading="loading">
          <el-table-column type="selection" width="50" />
          <el-table-column prop="code" label="用例编号" width="150" />
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column
            v-if="visibleColumns.includes('case_type')"
            prop="case_type"
            label="用例类型"
            width="120"
          />
          <el-table-column
            v-if="visibleColumns.includes('platform')"
            prop="platform"
            label="平台"
            width="100"
          />
          <el-table-column
            v-if="visibleColumns.includes('priority')"
            prop="priority"
            label="优先级"
            width="80"
          >
            <template #default="{ row }">
              <el-tag :type="getPriorityType(row.priority)">
                {{ row.priority }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            v-if="visibleColumns.includes('owner')"
            prop="owner"
            label="维护人"
            width="100"
          />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="handleEditCase(row)">编辑</el-button>
              <el-button size="small" @click="handleCopyCase(row)">复制</el-button>
              <el-button size="small" @click="handleMoveCase(row)">移动</el-button>
              <el-button size="small" type="danger" @click="handleDeleteCase(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-empty v-else description="请选择左侧分组" />
    </div>

    <!-- 分组编辑对话框 -->
    <el-dialog
      v-model="groupDialogVisible"
      :title="groupForm.id ? '编辑分组' : '新增分组'"
      width="400px"
    >
      <el-form :model="groupForm" label-width="80px">
        <el-form-item label="分组名称">
          <el-input v-model="groupForm.name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="groupDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveGroup">保存</el-button>
      </template>
    </el-dialog>

    <!-- 移动用例对话框 -->
    <el-dialog v-model="moveDialogVisible" title="移动用例" width="400px">
      <el-tree
        :data="groupTree"
        :props="{ label: 'label', children: 'children' }"
        node-key="id"
        highlight-current
        @node-click="handleSelectMoveTarget"
      />
      <template #footer>
        <el-button @click="moveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmMove">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ArrowDown } from '@element-plus/icons-vue'
import { testcaseApi, TreeNode, TestCase, TestCaseGroup } from '@/api/testcase'
import { useRouter } from 'vue-router'

const router = useRouter()

// 状态
const groupTree = ref<TreeNode[]>([])
const caseList = ref<TestCase[]>([])
const selectedGroup = ref<TreeNode | null>(null)
const loading = ref(false)
const searchKeyword = ref('')
const treeRef = ref()

// 分组对话框
const groupDialogVisible = ref(false)
const groupForm = ref<Partial<TreeNode & { parent_id?: number }>>({})

// 移动对话框
const moveDialogVisible = ref(false)
const moveTarget = ref<TreeNode | null>(null)
const moveCaseId = ref<number | null>(null)

// 列设置
const allColumns = [
  { prop: 'case_type', label: '用例类型' },
  { prop: 'platform', label: '平台' },
  { prop: 'priority', label: '优先级' },
  { prop: 'owner', label: '维护人' },
  { prop: 'developer', label: '开发负责人' },
  { prop: 'is_core', label: '核心用例' },
  { prop: 'status', label: '状态' },
  { prop: 'updated_at', label: '更新时间' },
]
const visibleColumns = ref(['case_type', 'platform', 'priority', 'owner'])

// 加载分组树
const loadGroupTree = async () => {
  const { data } = await testcaseApi.getGroupTree()
  groupTree.value = data
}

// 加载用例列表
const loadCaseList = async (groupId: number) => {
  loading.value = true
  try {
    const { data } = await testcaseApi.getCases(groupId)
    caseList.value = data.items
  } finally {
    loading.value = false
  }
}

// 选择节点
const handleNodeClick = (node: TreeNode) => {
  selectedGroup.value = node
  loadCaseList(node.id)
}

// 新增分组
const handleAddGroup = () => {
  groupForm.value = { parent_id: null }
  groupDialogVisible.value = true
}

// 新增子分组
const handleAddSubGroup = (node: TreeNode) => {
  groupForm.value = { parent_id: node.id }
  groupDialogVisible.value = true
}

// 编辑分组
const handleEditGroup = (node: TreeNode) => {
  groupForm.value = { ...node }
  groupDialogVisible.value = true
}

// 保存分组
const handleSaveGroup = async () => {
  if (groupForm.value.id) {
    await testcaseApi.updateGroup(groupForm.value.id, { name: groupForm.value.label })
    ElMessage.success('更新成功')
  } else {
    await testcaseApi.createGroup({
      name: groupForm.value.label || '',
      parent_id: groupForm.value.parent_id
    })
    ElMessage.success('创建成功')
  }
  groupDialogVisible.value = false
  loadGroupTree()
}

// 删除分组
const handleDeleteGroup = async (node: TreeNode) => {
  await ElMessageBox.confirm('删除分组将同时删除所有子分组和用例，确定删除？', '提示')
  await testcaseApi.deleteGroup(node.id)
  ElMessage.success('删除成功')
  loadGroupTree()
}

// 新增用例
const handleAddCase = () => {
  router.push(`/testcase/create?group_id=${selectedGroup.value?.id}`)
}

// 编辑用例
const handleEditCase = (row: TestCase) => {
  router.push(`/testcase/${row.id}/edit`)
}

// 复制用例
const handleCopyCase = async (row: TestCase) => {
  await testcaseApi.copyCase(row.id)
  ElMessage.success('复制成功')
  loadCaseList(selectedGroup.value!.id)
}

// 移动用例
const handleMoveCase = (row: TestCase) => {
  moveCaseId.value = row.id
  moveDialogVisible.value = true
}

// 选择移动目标
const handleSelectMoveTarget = (node: TreeNode) => {
  moveTarget.value = node
}

// 确认移动
const handleConfirmMove = async () => {
  if (!moveTarget.value || !moveCaseId.value) return
  await testcaseApi.moveCase(moveCaseId.value, moveTarget.value.id)
  ElMessage.success('移动成功')
  moveDialogVisible.value = false
  loadCaseList(selectedGroup.value!.id)
}

// 删除用例
const handleDeleteCase = async (row: TestCase) => {
  await ElMessageBox.confirm('确定删除该用例？', '提示')
  await testcaseApi.deleteCase(row.id)
  ElMessage.success('删除成功')
  loadCaseList(selectedGroup.value!.id)
}

// 优先级标签类型
const getPriorityType = (priority: string) => {
  const types: Record<string, string> = {
    P0: 'danger',
    P1: 'warning',
    P2: '',
    P3: 'info',
    P4: 'info',
  }
  return types[priority] || ''
}

onMounted(() => {
  loadGroupTree()
})
</script>

<style scoped>
.testcase-container {
  display: flex;
  height: calc(100vh - 60px);
  padding: 20px;
  gap: 20px;
}

.left-panel {
  width: 300px;
  flex-shrink: 0;
}

.right-panel {
  flex: 1;
  overflow: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-input {
  margin-bottom: 12px;
}

.tree-node {
  display: flex;
  align-items: center;
  width: 100%;
  font-size: 14px;
}

.case-count {
  margin-left: 4px;
  color: #909399;
  font-size: 12px;
}

.node-actions {
  margin-left: auto;
  display: none;
}

.tree-node:hover .node-actions {
  display: flex;
}

.header-actions {
  display: flex;
  gap: 8px;
}
</style>
```

**Step 2: 更新路由**

```typescript
// 添加到 frontend/src/router/index.ts
{
  path: '/testcase',
  name: 'TestCase',
  component: () => import('@/views/testcase/index.vue')
},
```

**Step 3: 提交**

```bash
git add frontend/src/views/testcase/index.vue frontend/src/router/index.ts
git commit -m "feat(testcase): add testcase management main page"
```

---

## 总结

本实施计划覆盖了用例管理模块的完整实现：

**Phase 1: 数据模型层**
- Task 1: 用例分组模型
- Task 2: Pydantic Schemas

**Phase 2: 服务层**
- Task 3: 用例分组服务

**Phase 3: API 层**
- Task 4: API 路由

**Phase 4: 数据库迁移**
- Task 5: 创建数据库迁移

**Phase 5: 前端实现**
- Task 6: API 客户端
- Task 7: 用例管理主页面

**后续可扩展：**
- 用例编辑/详情页面
- 附件上传功能
- 富文本编辑器集成
- 批量导入/导出功能
