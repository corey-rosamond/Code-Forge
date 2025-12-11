# Code-Forge Architectural Plan
## A Clean Architecture Approach to AI-Assisted Development

**Document Version:** 1.0
**Architect:** Senior Architecture Team
**Date:** December 2025
**Methodology:** Domain-Driven Design with SOLID Principles

---

## Preface: Architectural Philosophy

After three decades in software architecture, I've learned that the difference between a good system and a great one lies not in its features, but in its fundamental architecture. Code-Forge represents an opportunity to build a system that exemplifies the best practices we've refined over the years.

This plan embraces:
- **SOLID Principles** as our foundation
- **Gang of Four Design Patterns** where they add value
- **Domain-Driven Design** for clear boundaries
- **Behavior-Driven Development** for verification
- **McCabe Complexity Metrics** keeping all methods under 10
- **Clean Architecture** for maintainability

Remember: *Architecture is about the important decisions, the ones that are hard to change.*

---

## 1. System Architecture Overview

### 1.1 Architectural Style: Hexagonal Architecture (Ports & Adapters)

```
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│  │Terminal │ │ FileIO  │ │ Network │ │Database│         │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘         │
│       │           │           │           │                │
│  ┌────▼───────────▼───────────▼───────────▼────┐         │
│  │            Adapter Layer (Ports)             │         │
│  └────┬───────────────────────────────────┬────┘         │
│       │                                   │                │
│  ┌────▼───────────────────────────────────▼────┐         │
│  │         Application Services Layer          │         │
│  │  ┌─────────────────────────────────────┐   │         │
│  │  │    Domain Model (Core Business)     │   │         │
│  │  │  ┌─────────┐ ┌─────────┐ ┌──────┐ │   │         │
│  │  │  │ Agent   │ │ Context │ │Tools │ │   │         │
│  │  │  │ Entity  │ │ Manager │ │System│ │   │         │
│  │  │  └─────────┘ └─────────┘ └──────┘ │   │         │
│  │  └─────────────────────────────────────┘   │         │
│  └──────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Core Design Principles

#### Single Responsibility Principle (SRP)
Each class has one, and only one, reason to change. Our `AgentOrchestrator` handles agent lifecycle, not UI or persistence.

#### Open-Closed Principle (OCP)
System is open for extension, closed for modification. New tools can be added without changing core interfaces.

#### Liskov Substitution Principle (LSP)
All model providers (OpenRouter, Direct API) are interchangeable through the `IModelProvider` interface.

#### Interface Segregation Principle (ISP)
Clients depend only on interfaces they use. Tools don't know about UI, UI doesn't know about persistence.

#### Dependency Inversion Principle (DIP)
High-level modules don't depend on low-level modules. Both depend on abstractions.

---

## 2. Domain Model Design

### 2.1 Core Domain Entities

```python
# Following Domain-Driven Design with Rich Domain Models

@dataclass
class Agent(Entity):
    """
    The Agent is our Aggregate Root - the heart of our domain.
    McCabe Complexity: Each method ≤ 6
    """
    id: AgentId
    name: str
    capabilities: Set[Capability]
    context: Context
    state: AgentState
    _events: List[DomainEvent] = field(default_factory=list)

    def execute_task(self, task: Task) -> TaskResult:
        """Execute with Chain of Responsibility pattern"""
        if not self.can_handle(task):
            raise CannotHandleTaskError(task)

        self._validate_preconditions(task)
        result = self._process_task(task)
        self._emit_event(TaskExecutedEvent(self.id, task, result))
        return result

    # McCabe = 3 (well under threshold)
    def can_handle(self, task: Task) -> bool:
        required = task.required_capabilities
        return required.issubset(self.capabilities)
```

### 2.2 Value Objects

```python
@dataclass(frozen=True)
class Context:
    """Immutable value object representing agent context"""
    tokens: List[Token]
    max_tokens: int
    compression_strategy: CompressionStrategy

    def with_tokens(self, new_tokens: List[Token]) -> 'Context':
        """Return new instance with updated tokens (Immutability)"""
        return Context(
            tokens=new_tokens,
            max_tokens=self.max_tokens,
            compression_strategy=self.compression_strategy
        )

    def requires_compression(self) -> bool:
        return len(self.tokens) > self.max_tokens * 0.8
```

### 2.3 Domain Services

```python
class ModelRoutingService:
    """
    Strategy Pattern for model selection
    Complexity kept low through composition
    """
    def __init__(self, strategies: List[IRoutingStrategy]):
        self._strategies = strategies

    def select_optimal_model(
        self,
        task: Task,
        constraints: Constraints
    ) -> Model:
        # Chain of Responsibility through strategies
        for strategy in self._strategies:
            if model := strategy.evaluate(task, constraints):
                return model
        return self._get_default_model()
```

---

## 3. Design Patterns Implementation

### 3.1 Command Pattern for Tools

```python
class IToolCommand(ABC):
    """Command interface for all tools"""
    @abstractmethod
    def execute(self, context: ExecutionContext) -> Result:
        pass

    @abstractmethod
    def can_undo(self) -> bool:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

class FileEditCommand(IToolCommand):
    """Concrete command with undo capability"""
    def __init__(self, file_path: Path, old_content: str, new_content: str):
        self._file_path = file_path
        self._old_content = old_content
        self._new_content = new_content
        self._backup: Optional[str] = None

    def execute(self, context: ExecutionContext) -> Result:
        self._backup = self._read_current_content()
        self._write_content(self._new_content)
        return Result.success()

    def can_undo(self) -> bool:
        return self._backup is not None

    def undo(self) -> None:
        if self._backup:
            self._write_content(self._backup)
```

### 3.2 Observer Pattern for Hooks

```python
class HookManager:
    """
    Observer pattern for extensibility
    Follows Dependency Inversion Principle
    """
    def __init__(self):
        self._observers: Dict[EventType, List[IHookObserver]] = defaultdict(list)

    def attach(self, event: EventType, observer: IHookObserver) -> None:
        self._observers[event].append(observer)

    def notify(self, event: Event) -> None:
        # Parallel execution for performance
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(obs.update, event)
                for obs in self._observers[event.type]
            ]
            # Collect results with timeout
            for future in as_completed(futures, timeout=60):
                self._handle_result(future)
```

### 3.3 Factory Pattern for Tool Creation

```python
class ToolFactory:
    """
    Abstract Factory for tool instantiation
    Enables plugin system without core changes
    """
    _registry: Dict[str, Type[ITool]] = {}

    @classmethod
    def register(cls, name: str, tool_class: Type[ITool]) -> None:
        """Self-registering factory pattern"""
        cls._registry[name] = tool_class

    @classmethod
    def create(cls, name: str, config: ToolConfig) -> ITool:
        if name not in cls._registry:
            raise UnknownToolError(name)

        tool_class = cls._registry[name]
        return tool_class(config)

# Auto-registration through decorators
@register_tool("file_read")
class FileReadTool(ITool):
    pass
```

### 3.4 Strategy Pattern for Context Management

```python
class ICompressionStrategy(ABC):
    """Strategy interface for context compression"""
    @abstractmethod
    def compress(self, context: Context) -> Context:
        pass

class SummaryCompressionStrategy(ICompressionStrategy):
    """Concrete strategy using LLM summarization"""
    def compress(self, context: Context) -> Context:
        summary = self._summarize_oldest_messages(context)
        return context.with_compressed_history(summary)

class SlidingWindowStrategy(ICompressionStrategy):
    """Concrete strategy using window-based truncation"""
    def compress(self, context: Context) -> Context:
        recent = self._get_recent_messages(context, window_size=50)
        return context.with_tokens(recent)
```

### 3.5 Decorator Pattern for Middleware

```python
class IMiddleware(ABC):
    """Base middleware interface"""
    @abstractmethod
    def process(self, request: Request, next: Callable) -> Response:
        pass

class LoggingMiddleware(IMiddleware):
    """Decorator adding logging capability"""
    def process(self, request: Request, next: Callable) -> Response:
        self._log_request(request)
        response = next(request)
        self._log_response(response)
        return response

class RateLimitMiddleware(IMiddleware):
    """Decorator adding rate limiting"""
    def __init__(self, rate_limiter: IRateLimiter):
        self._limiter = rate_limiter

    def process(self, request: Request, next: Callable) -> Response:
        if not self._limiter.allow(request):
            raise RateLimitExceeded()
        return next(request)
```

---

## 4. Behavior-Driven Development Specifications

### 4.1 Core Agent Behavior

```gherkin
Feature: Agent Task Execution
  As a developer
  I want the agent to execute tasks reliably
  So that I can trust the system with complex operations

  Background:
    Given an agent with file and bash capabilities
    And a valid OpenRouter API connection
    And proper security permissions configured

  Scenario: Simple file reading task
    Given a file "test.py" exists with content "print('hello')"
    When I ask the agent to "read test.py"
    Then the agent should use the FileReadTool
    And the response should contain "print('hello')"
    And the token count should be under 1000

  Scenario: Complex multi-step task
    Given I have a Python project with tests
    When I ask the agent to "run tests and fix any failures"
    Then the agent should:
      | Action                | Tool        | Verification            |
      | Read test files       | FileRead    | Tests identified        |
      | Execute tests         | Bash        | Failures captured       |
      | Analyze failures      | Internal    | Root cause found        |
      | Read source files     | FileRead    | Code understood         |
      | Fix issues            | FileEdit    | Changes applied         |
      | Re-run tests          | Bash        | Tests pass              |
    And the total time should be under 30 seconds

  Scenario: Context overflow handling
    Given the context is at 90% capacity
    When I submit a new large request
    Then the agent should trigger compression
    And maintain conversation continuity
    And preserve critical information
```

### 4.2 Security Behavior

```gherkin
Feature: Security and Permissions
  As a system administrator
  I want strong security controls
  So that the system cannot perform unauthorized actions

  Scenario: Denied operation attempt
    Given a deny rule for "rm -rf"
    When the agent attempts to execute "rm -rf /important"
    Then the operation should be blocked
    And a security event should be logged
    And the user should see "Operation denied by security policy"

  Scenario: Permission escalation request
    Given an ask rule for "git push"
    When the agent needs to push changes
    Then a permission prompt should appear
    And the operation waits for user confirmation
    And timeout after 30 seconds if no response
```

---

## 5. Component Architecture

### 5.1 Core Components with Responsibilities

```python
# Component boundaries following Conway's Law
# Each team owns a bounded context

class AgentOrchestrator:
    """
    Orchestrates agent lifecycle and coordination
    Single Responsibility: Agent management
    McCabe Complexity: ≤ 7 for all methods
    """
    def __init__(
        self,
        agent_factory: IAgentFactory,
        event_bus: IEventBus,
        metrics_collector: IMetricsCollector
    ):
        self._factory = agent_factory
        self._events = event_bus
        self._metrics = metrics_collector
        self._agents: Dict[AgentId, Agent] = {}

    @measure_complexity  # Decorator to enforce McCabe ≤ 10
    def create_agent(self, spec: AgentSpec) -> Agent:
        # Complexity: 4
        agent = self._factory.create(spec)
        self._agents[agent.id] = agent
        self._events.publish(AgentCreatedEvent(agent))
        self._metrics.increment('agents.created')
        return agent

class ContextManager:
    """
    Manages context window optimization
    Single Responsibility: Context state management
    """
    def __init__(
        self,
        compression_strategy: ICompressionStrategy,
        token_counter: ITokenCounter
    ):
        self._strategy = compression_strategy
        self._counter = token_counter
        self._state = ContextState.NORMAL

    def optimize(self, context: Context) -> Context:
        # Complexity: 5 - Well within limits
        token_count = self._counter.count(context)

        if token_count > context.max_tokens:
            return self._handle_overflow(context)
        elif self._should_compress(token_count, context.max_tokens):
            return self._strategy.compress(context)
        else:
            return context
```

### 5.2 Repository Pattern for Persistence

```python
class ISessionRepository(ABC):
    """Repository interface for session persistence"""
    @abstractmethod
    async def save(self, session: Session) -> None:
        pass

    @abstractmethod
    async def load(self, session_id: SessionId) -> Session:
        pass

    @abstractmethod
    async def list_recent(self, limit: int) -> List[SessionSummary]:
        pass

class FileSystemSessionRepository(ISessionRepository):
    """Concrete implementation using file system"""
    def __init__(self, base_path: Path):
        self._base = base_path
        self._serializer = SessionSerializer()

    async def save(self, session: Session) -> None:
        path = self._get_session_path(session.id)
        async with aiofiles.open(path, 'w') as f:
            await f.write(self._serializer.serialize(session))

    async def load(self, session_id: SessionId) -> Session:
        path = self._get_session_path(session_id)
        async with aiofiles.open(path, 'r') as f:
            data = await f.read()
        return self._serializer.deserialize(data)
```

### 5.3 Adapter Pattern for Model Providers

```python
class IModelProvider(ABC):
    """Common interface for all model providers"""
    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        pass

class OpenRouterAdapter(IModelProvider):
    """
    Adapter for OpenRouter API
    Uses httpx for HTTP/2 support and type-safe async requests
    """
    def __init__(self, client: OpenRouterClient, config: OpenRouterConfig):
        self._client = client  # httpx.AsyncClient with HTTP/2
        self._config = config

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        # Transform to OpenRouter format
        or_request = self._transform_request(request)

        # Apply routing variant (:nitro, :floor, :exacto, :thinking, :online)
        or_request.model = self._apply_routing_strategy(
            request.intent,
            self._config.routing_preference
        )

        # Execute with retry logic
        response = await self._client.chat_completion(or_request)

        # Transform back to common format
        return self._transform_response(response)

class DirectAnthropicAdapter(IModelProvider):
    """Adapter for direct Anthropic API"""
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        # Different implementation, same interface
        pass
```

---

## 6. Testing Strategy

### 6.1 Test Pyramid

```
         /\
        /UI\        <- 10% - E2E Tests
       /────\
      /Integr\      <- 20% - Integration Tests
     /────────\
    /Unit Tests\    <- 70% - Unit Tests
   /────────────\
```

### 6.2 Unit Testing Approach

```python
class TestAgentOrchestrator:
    """
    Unit tests with mocks for isolation
    Each test method has single assertion (SRP for tests)
    """

    @pytest.fixture
    def orchestrator(self, mock_factory, mock_event_bus, mock_metrics):
        return AgentOrchestrator(mock_factory, mock_event_bus, mock_metrics)

    def test_create_agent_publishes_event(self, orchestrator, mock_event_bus):
        # Arrange
        spec = AgentSpec(name="test", capabilities={"read"})

        # Act
        agent = orchestrator.create_agent(spec)

        # Assert - Single assertion per test
        mock_event_bus.publish.assert_called_once_with(
            IsInstance(AgentCreatedEvent)
        )

    def test_create_agent_increments_metrics(self, orchestrator, mock_metrics):
        # Arrange
        spec = AgentSpec(name="test", capabilities={"read"})

        # Act
        orchestrator.create_agent(spec)

        # Assert
        mock_metrics.increment.assert_called_once_with('agents.created')
```

### 6.3 Integration Testing

```python
@pytest.mark.integration
class TestOpenRouterIntegration:
    """Integration tests with real OpenRouter API"""

    @pytest.fixture
    async def provider(self):
        config = OpenRouterConfig.from_env()
        client = OpenRouterClient(config)
        return OpenRouterAdapter(client, config)

    async def test_simple_completion(self, provider):
        # Real API call with minimal tokens
        request = CompletionRequest(
            prompt="Say 'test'",
            max_tokens=10
        )

        response = await provider.complete(request)

        assert "test" in response.text.lower()
        assert response.token_count < 20
```

### 6.4 Property-Based Testing

```python
from hypothesis import given, strategies as st

class TestContextCompression:
    """Property-based tests for invariants"""

    @given(
        tokens=st.lists(st.text(), min_size=100, max_size=1000),
        max_tokens=st.integers(min_value=50, max_value=500)
    )
    def test_compression_reduces_tokens(self, tokens, max_tokens):
        # Property: Compression always reduces token count
        context = Context(tokens=tokens, max_tokens=max_tokens)
        strategy = SummaryCompressionStrategy()

        compressed = strategy.compress(context)

        assert len(compressed.tokens) <= len(context.tokens)
        assert len(compressed.tokens) <= max_tokens
```

---

## 7. Performance Architecture

### 7.1 Caching Strategy

```python
class CacheManager:
    """
    Multi-level caching with Cache-Aside pattern
    L1: In-memory (LRU)
    L2: Redis
    L3: Disk
    """
    def __init__(self):
        self._l1 = LRUCache(maxsize=1000)
        self._l2 = RedisCache()
        self._l3 = DiskCache()

    async def get(self, key: str) -> Optional[Any]:
        # Check each level
        if value := self._l1.get(key):
            return value

        if value := await self._l2.get(key):
            self._l1.put(key, value)  # Promote to L1
            return value

        if value := await self._l3.get(key):
            await self._l2.put(key, value)  # Promote to L2
            self._l1.put(key, value)  # Promote to L1
            return value

        return None
```

### 7.2 Async/Await Architecture

```python
class AsyncPipeline:
    """
    Asynchronous processing pipeline
    Maintains McCabe complexity ≤ 8
    """
    def __init__(self):
        self._stages: List[IStage] = []

    async def process(self, input: Input) -> Output:
        # Complexity: 3
        result = input
        for stage in self._stages:
            result = await stage.process(result)
        return result

    async def process_parallel(self, inputs: List[Input]) -> List[Output]:
        # Complexity: 4
        tasks = [self.process(inp) for inp in inputs]
        return await asyncio.gather(*tasks)
```

### 7.3 Performance Monitoring

```python
class PerformanceMonitor:
    """
    Tracks performance metrics with minimal overhead
    Uses decorator pattern for non-intrusive monitoring
    """

    @staticmethod
    def measure(metric_name: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.perf_counter() - start
                    Metrics.record(metric_name, duration)
                    return result
                except Exception as e:
                    Metrics.increment(f"{metric_name}.errors")
                    raise
            return wrapper
        return decorator
```

---

## 8. Security Architecture

### 8.1 Defense in Depth

```python
class SecurityLayer:
    """
    Multiple security layers following Defense in Depth
    Each layer independent (Fail-Safe defaults)
    """

    def __init__(self):
        self._layers = [
            InputSanitizer(),       # Layer 1: Input validation
            PermissionChecker(),    # Layer 2: Authorization
            RateLimiter(),         # Layer 3: Rate limiting
            SandboxExecutor(),     # Layer 4: Execution isolation
            AuditLogger()          # Layer 5: Audit trail
        ]

    async def execute(self, command: Command) -> Result:
        # Each layer can reject independently
        for layer in self._layers:
            if not await layer.validate(command):
                raise SecurityViolation(layer.name)

        return await self._execute_safe(command)
```

### 8.2 Principle of Least Privilege

```python
class PermissionManager:
    """
    Implements least privilege with explicit grants
    Default deny for unspecified permissions
    """

    def check_permission(self, action: Action, context: Context) -> bool:
        # Complexity: 6
        if self._is_explicitly_denied(action):
            return False

        if self._is_explicitly_allowed(action):
            return True

        if self._requires_user_confirmation(action):
            return self._prompt_user(action, context)

        # Default deny
        return False
```

---

## 9. Scalability Considerations

### 9.1 Horizontal Scaling Architecture

```python
class WorkerPool:
    """
    Distributed worker pool for horizontal scaling
    Uses Actor pattern for worker management
    """

    def __init__(self, min_workers: int = 2, max_workers: int = 10):
        self._min = min_workers
        self._max = max_workers
        self._workers: List[Worker] = []
        self._load_balancer = RoundRobinBalancer()

    async def scale(self, load: float) -> None:
        # Auto-scaling based on load
        target = self._calculate_target_workers(load)
        current = len(self._workers)

        if target > current:
            await self._spawn_workers(target - current)
        elif target < current:
            await self._terminate_workers(current - target)
```

### 9.2 Event-Driven Architecture

```python
class EventBus:
    """
    Central event bus for loose coupling
    Enables microservice migration path
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[ISubscriber]] = defaultdict(list)
        self._queue = asyncio.Queue()
        self._running = False

    async def publish(self, event: Event) -> None:
        await self._queue.put(event)

    async def start(self) -> None:
        self._running = True
        while self._running:
            event = await self._queue.get()
            await self._dispatch(event)

    async def _dispatch(self, event: Event) -> None:
        # Fan-out to all subscribers
        tasks = [
            sub.handle(event)
            for sub in self._subscribers[event.type]
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
```

---

## 10. Maintainability Metrics

### 10.1 Code Complexity Targets

```python
# Automated complexity checking
class ComplexityChecker:
    """
    Enforces McCabe complexity limits
    Part of CI/CD pipeline
    """

    MAX_COMPLEXITY = {
        'default': 10,
        'core': 8,      # Stricter for core components
        'utils': 12,    # More lenient for utilities
    }

    def check_module(self, module_path: Path) -> List[Violation]:
        violations = []
        tree = ast.parse(module_path.read_text())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                limit = self._get_limit(module_path)

                if complexity > limit:
                    violations.append(
                        Violation(
                            file=module_path,
                            function=node.name,
                            complexity=complexity,
                            limit=limit
                        )
                    )

        return violations
```

### 10.2 Maintainability Index

```
MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(L)

Where:
- V = Halstead Volume
- G = Cyclomatic Complexity
- L = Lines of Code

Target: MI > 80 (Highly Maintainable)
```

---

## 11. Deployment Architecture

### 11.1 Container Architecture

```dockerfile
# Multi-stage build for security and size optimization
# Python 3.10+ minimum (LangChain 1.0), 3.11+ recommended for performance
FROM python:3.11-slim as builder

# Build stage - compile dependencies
WORKDIR /build
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction

# Runtime stage - minimal attack surface
FROM python:3.11-slim

# Security: Non-root user
RUN useradd -m -u 1000 forge
USER forge

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --chown=forge:forge . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import sys; sys.exit(0)"

ENTRYPOINT ["python", "-m", "forge"]
```

### 11.2 Orchestration with Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: forge
  labels:
    app: forge
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: forge
  template:
    metadata:
      labels:
        app: forge
    spec:
      containers:
      - name: forge
        image: forge:latest
        resources:
          limits:
            memory: "2Gi"
            cpu: "1000m"
          requests:
            memory: "512Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 12. Development Workflow

### 12.1 Git Flow Strategy

```
main
  │
  ├─ develop
  │    │
  │    ├─ feature/add-openrouter-client
  │    ├─ feature/implement-mcp-protocol
  │    └─ feature/langchain-middleware
  │
  ├─ release/1.0.0
  │
  └─ hotfix/security-patch
```

### 12.2 Continuous Integration Pipeline

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check Complexity
        run: |
          python -m mccabe --max-complexity 10 src/

      - name: Type Checking
        run: |
          mypy src/ --strict

      - name: Code Coverage
        run: |
          pytest --cov=src --cov-report=xml
          coverage report --fail-under=80

      - name: Security Scan
        run: |
          bandit -r src/
          safety check

      - name: Performance Tests
        run: |
          pytest tests/performance/ --benchmark-only
```

---

## 13. Risk Mitigation

### 13.1 Technical Debt Management

```python
class TechnicalDebtTracker:
    """
    Tracks and manages technical debt
    Integrates with issue tracking
    """

    def __init__(self):
        self._debt_items: List[DebtItem] = []
        self._threshold = DebtThreshold(
            critical=10,  # Stop-ship if exceeded
            high=25,      # Priority fix
            medium=50     # Plan for next sprint
        )

    @property
    def debt_score(self) -> int:
        return sum(item.impact * item.likelihood for item in self._debt_items)

    def add_debt(self, item: DebtItem) -> None:
        self._debt_items.append(item)

        if self.debt_score > self._threshold.critical:
            raise CriticalDebtException(
                "Technical debt exceeds critical threshold"
            )
```

### 13.2 Architectural Decision Records (ADR)

```markdown
# ADR-001: Use Hexagonal Architecture

## Status
Accepted

## Context
Need clear separation between domain logic and infrastructure.

## Decision
Implement Hexagonal Architecture (Ports & Adapters).

## Consequences
- **Positive**: Technology agnostic core, easy testing, clear boundaries
- **Negative**: Initial complexity, more interfaces

## Metrics
- Coupling: < 0.2 (Low)
- Cohesion: > 0.8 (High)
- Testability: > 90% coverage possible
```

---

## 14. Quality Metrics

### 14.1 SOLID Compliance Score

```python
def calculate_solid_score(codebase: Codebase) -> float:
    """
    Calculate SOLID principles compliance
    Target: > 0.85 (85%)
    """
    scores = {
        'srp': measure_single_responsibility(codebase),    # > 0.9
        'ocp': measure_open_closed(codebase),              # > 0.85
        'lsp': measure_liskov_substitution(codebase),      # > 0.95
        'isp': measure_interface_segregation(codebase),    # > 0.8
        'dip': measure_dependency_inversion(codebase)      # > 0.85
    }

    return sum(scores.values()) / len(scores)
```

### 14.2 Maintainability Dashboard

```
┌─────────────────────────────────────────┐
│        Code-Forge Quality Dashboard        │
├─────────────────────────────────────────┤
│ McCabe Complexity:      7.2/10.0   ✓    │
│ Test Coverage:          86%        ✓    │
│ SOLID Score:           0.88        ✓    │
│ Technical Debt:        Low         ✓    │
│ Documentation:         92%         ✓    │
│ Security Score:        A           ✓    │
│ Performance:          <2s p99      ✓    │
│ Maintainability Index: 85          ✓    │
└─────────────────────────────────────────┘
```

---

## 15. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- Core domain model
- Basic SOLID architecture
- Command pattern for tools
- Simple REPL

### Phase 2: Patterns (Weeks 3-4)
- Observer pattern for hooks
- Strategy pattern for routing
- Factory pattern for tools
- Adapter pattern for providers

### Phase 3: Integration (Weeks 5-6)
- OpenRouter integration
- LangChain middleware
- MCP protocol
- Git integration

### Phase 4: Quality (Weeks 7-8)
- 80% test coverage
- Performance optimization
- Security hardening
- Documentation

### Phase 5: Polish (Weeks 9-10)
- UI/UX refinement
- Beta testing
- Bug fixes
- Release preparation

---

## Conclusion

This architecture represents three decades of lessons learned. It's not about using every pattern or principle, but about applying the right ones at the right time. The key is:

1. **Keep it Simple** - But not simpler than necessary
2. **Make it Testable** - If it's hard to test, it's wrong
3. **Design for Change** - The only constant is change
4. **Measure Everything** - You can't improve what you don't measure

Remember: *Clean code always looks like it was written by someone who cares.*

The architecture proposed here will result in a system that is:
- **Maintainable** - McCabe ≤ 10, MI > 80
- **Extensible** - Open/Closed Principle throughout
- **Testable** - 80%+ coverage achievable
- **Performant** - <2s response time
- **Secure** - Defense in depth

This is not just a plan—it's a commitment to excellence.

---

*"Any fool can write code that a computer can understand. Good programmers write code that humans can understand."* — Martin Fowler

---

## Appendix A: Design Pattern Quick Reference

| Pattern | Usage in Code-Forge | Benefit |
|---------|------------------|---------|
| Command | Tool execution | Undo/redo, queuing |
| Observer | Hook system | Loose coupling |
| Strategy | Model routing | Algorithm selection |
| Factory | Tool creation | Plugin system |
| Adapter | API providers | Interface uniformity |
| Decorator | Middleware | Feature composition |
| Repository | Persistence | Data abstraction |
| Template Method | Base classes | Code reuse |

## Appendix B: SOLID Checklist

- [ ] Each class has single responsibility
- [ ] New features via extension, not modification
- [ ] Derived classes substitutable for base
- [ ] Interfaces are client-specific
- [ ] Depend on abstractions, not concretions

## Appendix C: Complexity Guidelines

| Component Type | Max McCabe | Max LOC | Max Dependencies |
|---------------|-----------|---------|-----------------|
| Core Domain | 8 | 100 | 3 |
| Application | 10 | 150 | 5 |
| Infrastructure | 12 | 200 | 7 |
| Tests | 5 | 50 | 2 |

---

*Document Version: 1.0*
*Last Updated: December 2025*
*Next Review: Q1 2026*
*Approval: Architecture Board*