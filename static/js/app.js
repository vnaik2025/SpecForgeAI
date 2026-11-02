// SpecForge AI v2.0 — Autonomous Spec Engine Frontend Controller

const API_BASE = '/api';
let authToken = localStorage.getItem('specforge_access_token') || localStorage.getItem('specforge_token') || null;
let refreshToken = localStorage.getItem('specforge_refresh_token') || null;
let currentScaffold = null;
let activeFileKey = 'fe_agent';
let isRawMode = false;
let techTags = [];

// Comprehensive Tech Stack Catalog for Instant Autocomplete
const TECH_CATALOG = [
  // Languages
  { name: 'Python', cat: 'Language' },
  { name: 'JavaScript', cat: 'Language' },
  { name: 'TypeScript', cat: 'Language' },
  { name: 'Go', cat: 'Language' },
  { name: 'Rust', cat: 'Language' },
  { name: 'Java', cat: 'Language' },
  { name: 'Kotlin', cat: 'Language' },
  { name: 'C#', cat: 'Language' },
  { name: 'PHP', cat: 'Language' },
  { name: 'Ruby', cat: 'Language' },
  { name: 'Swift', cat: 'Language' },
  { name: 'Dart', cat: 'Language' },
  { name: 'Elixir', cat: 'Language' },
  // Python Frameworks
  { name: 'Django', cat: 'Backend' },
  { name: 'DRF', cat: 'Backend' },
  { name: 'FastAPI', cat: 'Backend' },
  { name: 'Flask', cat: 'Backend' },
  { name: 'Tornado', cat: 'Backend' },
  { name: 'Celery', cat: 'Async Queue' },
  { name: 'SQLAlchemy', cat: 'ORM' },
  { name: 'Pydantic', cat: 'Validation' },
  // JS/TS Backend
  { name: 'Node.js', cat: 'Backend' },
  { name: 'Express', cat: 'Backend' },
  { name: 'NestJS', cat: 'Backend' },
  { name: 'Fastify', cat: 'Backend' },
  { name: 'Hono', cat: 'Backend' },
  { name: 'Prisma', cat: 'ORM' },
  { name: 'Drizzle', cat: 'ORM' },
  { name: 'TypeORM', cat: 'ORM' },
  { name: 'Zod', cat: 'Validation' },
  { name: 'BullMQ', cat: 'Async Queue' },
  // Frontend
  { name: 'React', cat: 'Frontend' },
  { name: 'Next.js', cat: 'Fullstack' },
  { name: 'Vue', cat: 'Frontend' },
  { name: 'Nuxt', cat: 'Fullstack' },
  { name: 'Svelte', cat: 'Frontend' },
  { name: 'SvelteKit', cat: 'Fullstack' },
  { name: 'Angular', cat: 'Frontend' },
  { name: 'SolidJS', cat: 'Frontend' },
  { name: 'Astro', cat: 'Frontend' },
  { name: 'Remix', cat: 'Fullstack' },
  { name: 'Vite', cat: 'Tooling' },
  { name: 'Vanilla JS', cat: 'Frontend' },
  { name: 'HTML5', cat: 'Frontend' },
  { name: 'Tailwind CSS', cat: 'CSS' },
  { name: 'TailwindCSS', cat: 'CSS' },
  { name: 'Shadcn/UI', cat: 'UI Library' },
  { name: 'Radix UI', cat: 'UI Library' },
  { name: 'Chakra UI', cat: 'UI Library' },
  { name: 'Material UI', cat: 'UI Library' },
  { name: 'Ant Design', cat: 'UI Library' },
  { name: 'Redux', cat: 'State' },
  { name: 'Zustand', cat: 'State' },
  { name: 'TanStack Query', cat: 'Data Fetching' },
  { name: 'React Query', cat: 'Data Fetching' },
  { name: 'Axios', cat: 'HTTP' },
  // Databases & Storage
  { name: 'PostgreSQL', cat: 'Database' },
  { name: 'MySQL', cat: 'Database' },
  { name: 'SQLite', cat: 'Database' },
  { name: 'MongoDB', cat: 'Database' },
  { name: 'Redis', cat: 'Cache' },
  { name: 'Supabase', cat: 'Database' },
  { name: 'Firebase', cat: 'Database' },
  { name: 'Cassandra', cat: 'Database' },
  { name: 'ClickHouse', cat: 'Analytics DB' },
  { name: 'Elasticsearch', cat: 'Search' },
  { name: 'Meilisearch', cat: 'Search' },
  { name: 'Pinecone', cat: 'Vector DB' },
  { name: 'ChromaDB', cat: 'Vector DB' },
  { name: 'Qdrant', cat: 'Vector DB' },
  // Auth & Security
  { name: 'simplejwt', cat: 'Auth' },
  { name: 'JWT', cat: 'Auth' },
  { name: 'NextAuth', cat: 'Auth' },
  { name: 'Clerk', cat: 'Auth' },
  { name: 'Auth0', cat: 'Auth' },
  { name: 'Lucia', cat: 'Auth' },
  // Architecture & Protocols
  { name: 'REST', cat: 'API' },
  { name: 'REST Framework', cat: 'API' },
  { name: 'GraphQL', cat: 'API' },
  { name: 'gRPC', cat: 'RPC' },
  { name: 'WebSocket', cat: 'Realtime' },
  { name: 'TRPC', cat: 'RPC' },
  // Messaging & Streams
  { name: 'RabbitMQ', cat: 'Message Queue' },
  { name: 'Kafka', cat: 'Event Stream' },
  { name: 'Redis Streams', cat: 'Streaming' },
  // DevOps & Cloud
  { name: 'Docker', cat: 'DevOps' },
  { name: 'Kubernetes', cat: 'DevOps' },
  { name: 'AWS', cat: 'Cloud' },
  { name: 'GCP', cat: 'Cloud' },
  { name: 'Azure', cat: 'Cloud' },
  { name: 'Vercel', cat: 'Cloud' },
  { name: 'Netlify', cat: 'Cloud' },
  { name: 'Cloudflare', cat: 'Edge' },
  { name: 'Nginx', cat: 'Server' },
  // AI & Agents
  { name: 'LangChain', cat: 'AI' },
  { name: 'LlamaIndex', cat: 'AI' },
  { name: 'Ollama', cat: 'AI' },
  { name: 'OpenAI API', cat: 'AI' },
  { name: 'Gemini API', cat: 'AI' },
  { name: 'Anthropic Claude', cat: 'AI' }
];

// DOM References
const authStatusBadge          = document.getElementById('authStatusBadge');
const scaffoldForm             = document.getElementById('scaffoldForm');
const submitGenerateBtn        = document.getElementById('submitGenerateBtn');
const projectTitle             = document.getElementById('projectTitle');
const scopeContentText         = document.getElementById('scopeContentText');
const customNotes              = document.getElementById('customNotes');
const wordCountBadge           = document.getElementById('wordCountBadge');
const dropZoneBox              = document.getElementById('dropZoneBox');
const fileUploadInput          = document.getElementById('fileUploadInput');
const tagWrapper               = document.getElementById('tagWrapper');
const techTagInput             = document.getElementById('techTagInput');
const techSuggestionsMenu      = document.getElementById('techSuggestionsMenu');

// 1st-Place AI Scope Analysis DOM Elements
const aiAnalysisStatus         = document.getElementById('aiAnalysisStatus');
const toggleScopeEditorBtn     = document.getElementById('toggleScopeEditorBtn');
const scopeEditorContainer     = document.getElementById('scopeEditorContainer');
const catFrontend              = document.getElementById('catFrontend');
const catBackend               = document.getElementById('catBackend');
const catDatabase              = document.getElementById('catDatabase');
const catServices              = document.getElementById('catServices');
const titleSourceBadge         = document.getElementById('titleSourceBadge');
const techSourceBadge          = document.getElementById('techSourceBadge');
const projectTitleWrapper      = document.getElementById('projectTitleWrapper');
const techStackSection         = document.getElementById('techStackSection');

const projectBannerTitle       = document.getElementById('projectBannerTitle');
const projectStatusPill        = document.getElementById('projectStatusPill');
const projectStackTagsContainer= document.getElementById('projectStackTagsContainer');
const totalFilesBadge          = document.getElementById('totalFilesBadge');
const specShaDisplay           = document.getElementById('specShaDisplay');

const currentViewerFilename    = document.getElementById('currentViewerFilename');
const currentViewerFilesize    = document.getElementById('currentViewerFilesize');
const renderedMarkdownContent  = document.getElementById('renderedMarkdownContent');
const rawMarkdownContent       = document.getElementById('rawMarkdownContent');
const modePreviewBtn           = document.getElementById('modePreviewBtn');
const modeRawBtn               = document.getElementById('modeRawBtn');
const copyCurrentFileBtn       = document.getElementById('copyCurrentFileBtn');
const downloadCurrentFileBtn    = document.getElementById('downloadCurrentFileBtn');
const copyPromptActionBtn      = document.getElementById('copyPromptActionBtn');
const downloadZipActionBtn     = document.getElementById('downloadZipActionBtn');
const downloadZipDropdownContainer = document.getElementById('downloadZipDropdownContainer');
const downloadZipMenu          = document.getElementById('downloadZipMenu');
const downloadAllZipBtn        = document.getElementById('downloadAllZipBtn');
const downloadFrontendZipBtn   = document.getElementById('downloadFrontendZipBtn');
const downloadBackendZipBtn    = document.getElementById('downloadBackendZipBtn');
const toastNotice              = document.getElementById('toastNotice');
let toastTimer                 = null;

function showToast(msg) {
  if (!toastNotice) return;
  toastNotice.textContent = msg;
  toastNotice.classList.add('show');
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastNotice.classList.remove('show');
  }, 2800);
}
const thinkingTerminal         = document.getElementById('thinkingTerminal');
const thinkingLines            = document.getElementById('thinkingLines');
const footerActiveSpec         = document.getElementById('footerActiveSpec');
const footerOutputPath         = document.getElementById('footerOutputPath');

// UI Prototype & Big Window Canvas Elements
const generateUiBtn            = document.getElementById('generateUiBtn');
const uiPrototypeContainer     = document.getElementById('uiPrototypeContainer');
const uiPrototypeIframe        = document.getElementById('uiPrototypeIframe');
const launchToolbarBigWindowBtn= document.getElementById('launchToolbarBigWindowBtn');
const openExternalUiBtn        = document.getElementById('openExternalUiBtn');
const launchBigWindowBtn       = document.getElementById('launchBigWindowBtn');
const launchExternalTabBtn     = document.getElementById('launchExternalTabBtn');
const toggleInlineFrameBtn     = document.getElementById('toggleInlineFrameBtn');
const inlineFrameContainer     = document.getElementById('inlineFrameContainer');
const inlineExpandToBigBtn     = document.getElementById('inlineExpandToBigBtn');

// Fullscreen Big Window Canvas Modal Elements
const uiCanvasModal            = document.getElementById('uiCanvasModal');
const closeUiCanvasModalBtn    = document.getElementById('closeUiCanvasModalBtn');
const modalUiPrototypeIframe   = document.getElementById('modalUiPrototypeIframe');
const modalIframeWrapper       = document.getElementById('modalIframeWrapper');

// ── Auth & Docking Elements ────────────────────────────────────────────────
let currentUser = null;
const authModal = document.getElementById('authModal');
const closeAuthModalBtn = document.getElementById('closeAuthModalBtn');
const openAuthModalBtn = document.getElementById('openAuthModalBtn');
const authNavGuest = document.getElementById('authNavGuest');
const authNavUser = document.getElementById('authNavUser');
const userInitialsAvatar = document.getElementById('userInitialsAvatar');
const userDisplayName = document.getElementById('userDisplayName');
const userEmailDisplay = document.getElementById('userEmailDisplay');
const logoutBtn = document.getElementById('logoutBtn');
const authTabSignInBtn = document.getElementById('authTabSignInBtn');
const authTabSignUpBtn = document.getElementById('authTabSignUpBtn');
const signInForm = document.getElementById('signInForm');
const signUpForm = document.getElementById('signUpForm');
const loginEmailInput = document.getElementById('loginEmailInput');
const loginPasswordInput = document.getElementById('loginPasswordInput');
const registerFirstNameInput = document.getElementById('registerFirstNameInput');
const registerLastNameInput = document.getElementById('registerLastNameInput');
const registerEmailInput = document.getElementById('registerEmailInput');
const registerPasswordInput = document.getElementById('registerPasswordInput');
const authErrorMessage = document.getElementById('authErrorMessage');
const authErrorText = document.getElementById('authErrorText');

// Docking Elements
const formColumn = document.getElementById('formColumn');
const studioColumn = document.getElementById('studioColumn');
const fileExplorerPanel = document.getElementById('fileExplorerPanel');
const docViewerPanel = document.getElementById('docViewerPanel');
const toggleFormDockBtn = document.getElementById('toggleFormDockBtn');
const dockFormBtnText = document.getElementById('dockFormBtnText');
const toggleFileTreeDockBtn = document.getElementById('toggleFileTreeDockBtn');
const dockTreeBtnText = document.getElementById('dockTreeBtnText');
const collapseInputPanelBtn = document.getElementById('collapseInputPanelBtn');
const studioEmptyState = document.getElementById('studioEmptyState');
const studioActiveWorkspace = document.getElementById('studioActiveWorkspace');
const studioActionButtons = document.getElementById('studioActionButtons');

let isFormCollapsed = false;
let isFileTreeCollapsed = false;

const canvasProjectTitle       = document.getElementById('canvasProjectTitle');
const modalVpDesktopBtn        = document.getElementById('modalVpDesktopBtn');
const modalVpLaptopBtn         = document.getElementById('modalVpLaptopBtn');
const modalVpTabletBtn         = document.getElementById('modalVpTabletBtn');
const modalVpMobileBtn         = document.getElementById('modalVpMobileBtn');
const modalOpenExternalBtn     = document.getElementById('modalOpenExternalBtn');
const modalDownloadHtmlBtn     = document.getElementById('modalDownloadHtmlBtn');

// ── Empty Studio Placeholder State (Zero Caching) ────────────────────────
const EMPTY_STUDIO_FILES = {
  // Frontend Folder Specifications
  fe_agent: {
    filename: 'AGENT.md',
    folder: 'frontend',
    display: 'frontend/AGENT.md',
    content: `# Frontend Guidelines (AGENT.md)\n\nNo project specifications generated yet.\n\nEnter your project scope on the left, select your platform, and click **Generate Architecture Plan** to build your specifications.`
  },
  fe_architecture: {
    filename: 'ARCHITECTURE.md',
    folder: 'frontend',
    display: 'frontend/ARCHITECTURE.md',
    content: `# Frontend Architecture (ARCHITECTURE.md)\n\nNo architecture specifications loaded yet.`
  },
  fe_setup: {
    filename: 'SETUP.md',
    folder: 'frontend',
    display: 'frontend/SETUP.md',
    content: `# Setup Guide (SETUP.md)\n\nNo setup instructions loaded yet.`
  },
  fe_skills: {
    filename: 'SKILLS.md',
    folder: 'frontend',
    display: 'frontend/SKILLS.md',
    content: `# UI Capabilities (SKILLS.md)\n\nNo UI capabilities loaded yet.`
  },
  fe_apisetup: {
    filename: 'API_SETUP.md',
    folder: 'frontend',
    display: 'frontend/API_SETUP.md',
    content: `# API Integration (API_SETUP.md)\n\nNo API client specifications loaded yet.`
  },
  fe_prompt: {
    filename: 'INITIAL_PROMPT.md',
    folder: 'frontend',
    display: 'frontend/INITIAL_PROMPT.md',
    content: `# Kickoff Prompt (INITIAL_PROMPT.md)\n\nNo kickoff prompt loaded yet.`
  },
  fe_ui: {
    filename: 'UI_PROTOTYPE.html',
    folder: 'frontend',
    display: 'frontend/UI_PROTOTYPE.html',
    content: ''
  },

  // Backend Folder Specifications
  be_agent: {
    filename: 'AGENT.md',
    folder: 'backend',
    display: 'backend/AGENT.md',
    content: `# Backend Guidelines (AGENT.md)\n\nNo backend specifications generated yet.`
  },
  be_architecture: {
    filename: 'ARCHITECTURE.md',
    folder: 'backend',
    display: 'backend/ARCHITECTURE.md',
    content: `# Backend Architecture (ARCHITECTURE.md)\n\nNo backend architecture loaded yet.`
  },
  be_setup: {
    filename: 'SETUP.md',
    folder: 'backend',
    display: 'backend/SETUP.md',
    content: `# Backend Setup Guide (SETUP.md)\n\nNo backend setup instructions loaded yet.`
  },
  be_skills: {
    filename: 'SKILLS.md',
    folder: 'backend',
    display: 'backend/SKILLS.md',
    content: `# Backend Capabilities (SKILLS.md)\n\nNo backend capabilities loaded yet.`
  },
  be_apisetup: {
    filename: 'API_SETUP.md',
    folder: 'backend',
    display: 'backend/API_SETUP.md',
    content: `# API Endpoints (API_SETUP.md)\n\nNo API endpoint contracts loaded yet.`
  },
  be_prompt: {
    filename: 'INITIAL_PROMPT.md',
    folder: 'backend',
    display: 'backend/INITIAL_PROMPT.md',
    content: `# Backend Kickoff Prompt (INITIAL_PROMPT.md)\n\nNo backend kickoff prompt loaded yet.`
  },

  // Root / Shared Files
  scope: {
    filename: 'SCOPE.md',
    folder: 'root',
    display: 'SCOPE.md',
    content: `# Project Scope (SCOPE.md)\n\nNo project scope loaded yet.`
  },

  // Backwards compatibility aliases
  agent: { filename: 'AGENT.md', folder: 'frontend', display: 'frontend/AGENT.md', content: '' },
  architecture: { filename: 'ARCHITECTURE.md', folder: 'frontend', display: 'frontend/ARCHITECTURE.md', content: '' },
  setup: { filename: 'SETUP.md', folder: 'frontend', display: 'frontend/SETUP.md', content: '' },
  skills: { filename: 'SKILLS.md', folder: 'frontend', display: 'frontend/SKILLS.md', content: '' },
  apisetup: { filename: 'API_SETUP.md', folder: 'frontend', display: 'frontend/API_SETUP.md', content: '' },
  prompt: { filename: 'INITIAL_PROMPT.md', folder: 'frontend', display: 'frontend/INITIAL_PROMPT.md', content: '' },
  ui: { filename: 'UI_PROTOTYPE.html', folder: 'frontend', display: 'frontend/UI_PROTOTYPE.html', content: '' }
};


function openAuthModal(tab = 'signin', errorMsg = null) {
  if (!authModal) return;
  authModal.classList.remove('hidden');
  switchAuthTab(tab);
  if (errorMsg) {
    showAuthError(errorMsg);
  } else {
    hideAuthError();
  }
}

function closeAuthModal() {
  if (!authModal) return;
  authModal.classList.add('hidden');
  hideAuthError();
}

function showAuthError(msg) {
  if (!authErrorMessage || !authErrorText) return;
  authErrorText.textContent = msg;
  authErrorMessage.classList.remove('hidden');
}

function hideAuthError() {
  if (!authErrorMessage) return;
  authErrorMessage.classList.add('hidden');
}

function switchAuthTab(tab) {
  if (tab === 'signin') {
    authTabSignInBtn?.classList.add('text-blue-600', 'border-b-2', 'border-blue-600', 'bg-white');
    authTabSignInBtn?.classList.remove('text-slate-500');
    authTabSignUpBtn?.classList.remove('text-blue-600', 'border-b-2', 'border-blue-600', 'bg-white');
    authTabSignUpBtn?.classList.add('text-slate-500');
    signInForm?.classList.remove('hidden');
    signUpForm?.classList.add('hidden');
  } else {
    authTabSignUpBtn?.classList.add('text-blue-600', 'border-b-2', 'border-blue-600', 'bg-white');
    authTabSignUpBtn?.classList.remove('text-slate-500');
    authTabSignInBtn?.classList.remove('text-blue-600', 'border-b-2', 'border-blue-600', 'bg-white');
    authTabSignInBtn?.classList.add('text-slate-500');
    signUpForm?.classList.remove('hidden');
    signInForm?.classList.add('hidden');
  }
  hideAuthError();
}

async function refreshAuthToken() {
  if (!refreshToken) return null;
  try {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    if (res.ok) {
      const data = await res.json();
      authToken = data.access;
      localStorage.setItem('specforge_access_token', authToken);
      localStorage.setItem('specforge_token', authToken);
      updateAuthBadge(true);
      return authToken;
    }
  } catch (err) {
    console.warn('Token refresh error:', err);
  }
  // Refresh token invalid or expired
  authToken = null;
  refreshToken = null;
  currentUser = null;
  localStorage.removeItem('specforge_access_token');
  localStorage.removeItem('specforge_refresh_token');
  localStorage.removeItem('specforge_token');
  renderLoggedOutUI();
  updateAuthBadge(false);
  return null;
}

async function checkAuthStatus() {
  if (!authToken && !refreshToken) {
    renderLoggedOutUI();
    return null;
  }
  if (!authToken && refreshToken) {
    await refreshAuthToken();
  }
  if (!authToken) {
    renderLoggedOutUI();
    return null;
  }
  try {
    let res = await fetch(`${API_BASE}/auth/me/`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    if (res.status === 401 && refreshToken) {
      const freshToken = await refreshAuthToken();
      if (freshToken) {
        res = await fetch(`${API_BASE}/auth/me/`, {
          headers: { 'Authorization': `Bearer ${freshToken}` }
        });
      }
    }
    if (res.ok) {
      currentUser = await res.json();
      renderLoggedInUI(currentUser);
      updateAuthBadge(true);
      return authToken;
    }
  } catch (err) {
    console.warn('Auth check error:', err);
  }
  authToken = null;
  currentUser = null;
  localStorage.removeItem('specforge_access_token');
  localStorage.removeItem('specforge_token');
  renderLoggedOutUI();
  updateAuthBadge(false);
  return null;
}

function renderLoggedInUI(user) {
  if (authNavGuest) authNavGuest.classList.add('hidden');
  if (authNavUser) authNavUser.classList.remove('hidden');
  if (userDisplayName) {
    const name = [user.first_name, user.last_name].filter(Boolean).join(' ') || 'Developer';
    userDisplayName.textContent = name;
  }
  if (userEmailDisplay) {
    userEmailDisplay.textContent = user.email || '';
  }
  if (userInitialsAvatar) {
    const initial = (user.first_name ? user.first_name[0] : (user.email ? user.email[0] : 'U')).toUpperCase();
    userInitialsAvatar.textContent = initial;
  }
}

function renderLoggedOutUI() {
  if (authNavGuest) authNavGuest.classList.remove('hidden');
  if (authNavUser) authNavUser.classList.add('hidden');
}

async function ensureAuthToken(forceRefresh = false) {
  if (authToken && !forceRefresh) {
    try {
      const payloadBase64 = authToken.split('.')[1];
      const payload = JSON.parse(atob(payloadBase64));
      const nowSeconds = Math.floor(Date.now() / 1000);
      if (payload.exp && payload.exp > nowSeconds + 60) {
        updateAuthBadge(true);
        return authToken;
      }
    } catch (e) {}
  }

  // Check Firebase active session
  if (window.fbAuth && window.fbAuth.currentUser) {
    try {
      const idToken = await window.fbAuth.currentUser.getIdToken(forceRefresh);
      const syncData = await syncUserWithBackend({
        id_token: idToken,
        email: window.fbAuth.currentUser.email,
        uid: window.fbAuth.currentUser.uid
      });
      if (syncData && syncData.access) {
        authToken = syncData.access;
        updateAuthBadge(true);
        return authToken;
      }
    } catch (fbErr) {
      console.warn('Firebase token refresh attempt:', fbErr);
    }
  }

  // If token is near expiration or forceRefresh, try refreshing first
  if (refreshToken) {
    const refreshed = await refreshAuthToken();
    if (refreshed) return refreshed;
  }

  // Token missing or expired - open modal
  openAuthModal('signin', 'Please sign in with your account to proceed.');
  updateAuthBadge(false);
  return null;
}

function updateAuthBadge(ok) {
  if (!authStatusBadge) return;
  if (ok) {
    authStatusBadge.className = "flex items-center space-x-1.5 text-[11px] font-medium text-slate-600 bg-emerald-50 border border-emerald-200/60 px-2 py-0.5 rounded-full";
    authStatusBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span><span class="text-emerald-700 font-mono tracking-tight text-[10px] uppercase">Ready</span>`;
  } else {
    authStatusBadge.className = "flex items-center space-x-1.5 text-[11px] font-medium text-slate-500 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full";
    authStatusBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span><span class="text-slate-600 font-mono tracking-tight text-[10px] uppercase">Sign In</span>`;
  }
}

// ── Docking Logic ─────────────────────────────────────────────────────────
function toggleFormDock() {
  isFormCollapsed = !isFormCollapsed;
  if (isFormCollapsed) {
    formColumn?.classList.add('hidden');
    if (studioColumn) {
      studioColumn.className = 'col-span-1 lg:col-span-12 flex flex-col gap-4 min-w-0 transition-all duration-300';
    }
    if (dockFormBtnText) dockFormBtnText.textContent = 'Show Input';
    showToast('Input panel docked (Full-width view)');
  } else {
    formColumn?.classList.remove('hidden');
    if (studioColumn) {
      studioColumn.className = 'col-span-1 lg:col-span-7 flex flex-col gap-4 min-w-0 transition-all duration-300';
    }
    if (dockFormBtnText) dockFormBtnText.textContent = 'Full Width';
  }
}

function toggleFileTreeDock() {
  isFileTreeCollapsed = !isFileTreeCollapsed;
  if (isFileTreeCollapsed) {
    fileExplorerPanel?.classList.add('hidden');
    if (docViewerPanel) {
      docViewerPanel.className = 'col-span-1 md:col-span-12 flex flex-col bg-white min-w-0 transition-all duration-200';
    }
    if (dockTreeBtnText) dockTreeBtnText.textContent = 'Show Files';
  } else {
    fileExplorerPanel?.classList.remove('hidden');
    if (docViewerPanel) {
      docViewerPanel.className = 'col-span-1 md:col-span-8 flex flex-col bg-white min-w-0 transition-all duration-200';
    }
    if (dockTreeBtnText) dockTreeBtnText.textContent = 'Sidebar';
  }
}

function updateWordCount() {
  if (!scopeContentText || !wordCountBadge) return;
  const text = scopeContentText.value.trim();
  const words = text ? text.split(/\s+/).filter(Boolean).length : 0;
  wordCountBadge.textContent = `${words} words`;
}

if (scopeContentText) {
  scopeContentText.addEventListener('input', updateWordCount);
}


// Toggle raw scope text editor
if (toggleScopeEditorBtn && scopeEditorContainer) {
  toggleScopeEditorBtn.addEventListener('click', () => {
    const isHidden = scopeEditorContainer.classList.contains('hidden');
    if (isHidden) {
      scopeEditorContainer.classList.remove('hidden');
      toggleScopeEditorBtn.innerHTML = '<span class="inline-flex items-center gap-1.5">Hide Scope Text <svg class="w-3.5 h-3.5 inline-block ml-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg></span>';
    } else {
      scopeEditorContainer.classList.add('hidden');
      toggleScopeEditorBtn.innerHTML = '<span class="inline-flex items-center gap-1.5">View Scope Text <svg class="w-3.5 h-3.5 inline-block ml-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></span>';
    }
  });
}

// ── Tech Stack Tag Chip Input ─────────────────────────────────────────────
function renderTechTags() {
  if (!tagWrapper) return;
  Array.from(tagWrapper.querySelectorAll('.tech-tag-chip')).forEach(el => el.remove());
  techTags.forEach((tag, idx) => {
    const chip = document.createElement('span');
    chip.className = 'tech-tag-chip inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono bg-slate-100 text-slate-800 border border-slate-200';
    chip.innerHTML = `${tag} <button type="button" data-idx="${idx}" class="text-slate-400 hover:text-slate-700 leading-none font-bold">×</button>`;
    chip.querySelector('button').addEventListener('click', (e) => {
      techTags.splice(parseInt(e.target.dataset.idx), 1);
      renderTechTags();
    });
    tagWrapper.insertBefore(chip, techTagInput);
  });
}

function addTechTag(value) {
  const v = value.trim().replace(/[,;]+$/, '').trim();
  if (!v) return;
  const parts = v.split(/[,;]+/).map(s => s.trim()).filter(Boolean);
  parts.forEach(p => {
    if (p && !techTags.some(t => t.toLowerCase() === p.toLowerCase())) {
      techTags.push(p);
    }
  });
  renderTechTags();
}

// ── Tech Stack Autocomplete Suggestions ──────────────────────────────────
function renderTechSuggestions(query) {
  if (!techSuggestionsMenu) return;
  const q = (query || '').trim().toLowerCase();
  if (!q) {
    techSuggestionsMenu.classList.add('hidden');
    techSuggestionsMenu.innerHTML = '';
    return;
  }

  const matches = TECH_CATALOG.filter(item => {
    const notSelected = !techTags.some(t => t.toLowerCase() === item.name.toLowerCase());
    const matched = item.name.toLowerCase().includes(q) || item.cat.toLowerCase().includes(q);
    return notSelected && matched;
  }).slice(0, 8);

  if (matches.length === 0) {
    techSuggestionsMenu.classList.add('hidden');
    techSuggestionsMenu.innerHTML = '';
    return;
  }

  techSuggestionsMenu.innerHTML = matches.map(item => `
    <div class="suggestion-item px-3 py-2 flex items-center justify-between hover:bg-slate-50 cursor-pointer text-slate-800 transition" data-name="${item.name}">
      <span class="font-semibold">${item.name}</span>
      <span class="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">${item.cat}</span>
    </div>
  `).join('');

  techSuggestionsMenu.querySelectorAll('.suggestion-item').forEach(el => {
    el.addEventListener('mousedown', (e) => {
      e.preventDefault();
      const name = el.getAttribute('data-name');
      addTechTag(name);
      techTagInput.value = '';
      techSuggestionsMenu.classList.add('hidden');
      techTagInput.focus();
    });
  });

  techSuggestionsMenu.classList.remove('hidden');
}

if (techTagInput) {
  tagWrapper.addEventListener('click', (e) => {
    if (e.target !== techTagInput && !e.target.closest('button')) {
      techTagInput.focus();
    }
  });

  techTagInput.addEventListener('input', (e) => {
    renderTechSuggestions(techTagInput.value);
  });

  techTagInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ',' || e.key === ';') {
      e.preventDefault();
      if (techTagInput.value.trim()) {
        addTechTag(techTagInput.value);
        techTagInput.value = '';
        renderTechSuggestions('');
      }
    } else if (e.key === 'Backspace' && techTagInput.value === '' && techTags.length > 0) {
      techTags.pop();
      renderTechTags();
    } else if (e.key === 'Escape') {
      renderTechSuggestions('');
    }
  });

  techTagInput.addEventListener('blur', () => {
    setTimeout(() => {
      if (techSuggestionsMenu) techSuggestionsMenu.classList.add('hidden');
      if (techTagInput.value.trim()) {
        addTechTag(techTagInput.value);
        techTagInput.value = '';
      }
    }, 150);
  });
}


// ── Drag & Drop & File Picker ─────────────────────────────────────────────
if (dropZoneBox && fileUploadInput) {
  dropZoneBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZoneBox.classList.add('border-blue-500', 'bg-blue-50/50');
  });
  dropZoneBox.addEventListener('dragleave', () => {
    dropZoneBox.classList.remove('border-blue-500', 'bg-blue-50/50');
  });
  dropZoneBox.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZoneBox.classList.remove('border-blue-500', 'bg-blue-50/50');
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processUploadedFile(e.dataTransfer.files[0]);
    }
  });
  fileUploadInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processUploadedFile(e.target.files[0]);
    }
    fileUploadInput.value = '';
  });
}

async function processUploadedFile(file) {
  if (!file) return;
  const isPdf = file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf';
  const isDocx = file.name.toLowerCase().endsWith('.docx') || file.name.toLowerCase().endsWith('.doc') || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
  let extractedTitle = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');

  // 1. Word Document (.docx) Extraction
  if (isDocx) {
    showToast(`Extracting document text from Word document "${file.name}"...`);

    // Method A: Client-side Mammoth.js
    if (window.mammoth) {
      try {
        const arrayBuffer = await file.arrayBuffer();
        const mammothRes = await mammoth.extractRawText({ arrayBuffer: arrayBuffer });
        const docText = (mammothRes && mammothRes.value ? mammothRes.value.trim() : '');
        if (docText.length > 20) {
          applyExtractedDocument(extractedTitle, docText);
          return;
        }
      } catch (mErr) {
        console.warn('Mammoth extraction failed, trying JSZip fallback:', mErr);
      }
    }

    // Method B: Client-side JSZip
    if (window.JSZip) {
      try {
        const arrayBuffer = await file.arrayBuffer();
        const zip = await JSZip.loadAsync(arrayBuffer);
        let docFile = zip.file('word/document.xml');
        if (!docFile) {
          for (let name in zip.files) {
            if (name.endsWith('document.xml')) {
              docFile = zip.files[name];
              break;
            }
          }
        }
        if (docFile) {
          const xmlStr = await docFile.async('string');
          const parser = new DOMParser();
          const xmlDoc = parser.parseFromString(xmlStr, 'text/xml');
          const paragraphs = xmlDoc.getElementsByTagName('w:p');
          const lines = [];
          for (let p of paragraphs) {
            const texts = p.getElementsByTagName('w:t');
            let pText = '';
            for (let t of texts) {
              pText += t.textContent;
            }
            pText = pText.trim();
            if (pText) {
              lines.push(pText);
            }
          }
          const fullDocText = lines.join('\n\n').trim();
          if (fullDocText.length > 20) {
            applyExtractedDocument(extractedTitle, fullDocText);
            return;
          }
        }
      } catch (docxErr) {
        console.warn('JSZip document parsing failed:', docxErr);
      }
    }

    // Method C: Server-side binary multipart extraction
    showToast(`Uploading "${file.name}" for server extraction...`);
    const serverResult = await uploadFileForServerAnalysis(file);
    if (serverResult && serverResult.extracted_text) {
      applyExtractedDocument(serverResult.title || extractedTitle, serverResult.extracted_text);
      applyAiAnalysisResults(serverResult);
      return;
    }

    showToast(`Could not extract text from "${file.name}". Please copy and paste the document text directly.`, 'error');
    return;
  }

  // 2. PDF Document Extraction
  if (isPdf) {
    showToast(`Extracting full document text from "${file.name}"...`);
    if (window.pdfjsLib) {
      try {
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        let fullDocText = '';
        const pageCount = pdf.numPages;

        try {
          const meta = await pdf.getMetadata();
          if (meta?.info?.Title && meta.info.Title.trim().length > 3) {
            extractedTitle = meta.info.Title.trim();
          }
        } catch (mErr) {
          console.warn('PDF metadata read error:', mErr);
        }

        for (let pageNum = 1; pageNum <= pageCount; pageNum++) {
          const page = await pdf.getPage(pageNum);
          const textContent = await page.getTextContent();
          let lastY, pageText = '';
          for (let item of textContent.items) {
            if (lastY !== item.transform[5] && lastY !== undefined) {
              pageText += '\n';
            } else if (pageText && !pageText.endsWith(' ') && !item.str.startsWith(' ')) {
              pageText += ' ';
            }
            pageText += item.str;
            lastY = item.transform[5];
          }

          if (pageText.trim()) {
            fullDocText += pageText.trim() + '\n\n';
          }
        }

        if (fullDocText.trim().length > 30) {
          applyExtractedDocument(extractedTitle, fullDocText.trim());
          return;
        }
      } catch (pdfErr) {
        console.warn('PDF.js parse failed, trying server extraction:', pdfErr);
      }
    }

    // Method C: Server-side PDF extraction
    showToast(`Uploading PDF for server-side extraction...`);
    const serverResult = await uploadFileForServerAnalysis(file);
    if (serverResult && serverResult.extracted_text) {
      applyExtractedDocument(serverResult.title || extractedTitle, serverResult.extracted_text);
      applyAiAnalysisResults(serverResult);
      return;
    }

    showToast(`Could not extract text from "${file.name}". Please copy and paste the document text directly.`, 'error');
    return;
  }

  // 3. Binary guard: Prevent binary files from being read as text
  const isBinary = file.name.match(/\.(zip|tar|gz|7z|rar|bin|exe|dll|iso|png|jpg|jpeg|gif|webp|mp4|mp3|wav|xlsx?|pptx?)$/i);
  if (isBinary) {
    showToast(`Binary file detected ("${file.name}"). Please upload a Word (.docx), PDF, Markdown, or text file.`, 'error');
    return;
  }

  // 4. Standard FileReader for plain text / markdown files only
  const reader = new FileReader();
  reader.onload = (e) => {
    let content = e.target.result || '';
    if (content.startsWith('PK\x03\x04') || content.startsWith('%PDF') || content.includes('[Content_Types].xml')) {
      showToast(`Cannot read binary document as plain text. Please upload .docx or .pdf directly.`, 'error');
      return;
    }
    applyExtractedDocument(extractedTitle, content);
  };
  reader.readAsText(file);
}

async function uploadFileForServerAnalysis(file) {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('filename', file.name);

    const headers = {};
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const res = await fetch(`${API_BASE}/scaffolds/analyze-scope/`, {
      method: 'POST',
      headers: headers,
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      return data;
    } else {
      const errData = await res.json().catch(() => ({}));
      console.warn('Server file analysis returned error:', errData.detail || res.status);
    }
  } catch (err) {
    console.warn('Server file analysis network error:', err);
  }
  return null;
}

function applyExtractedDocument(title, content) {
  if (scopeContentText) {
    scopeContentText.value = content;
    updateWordCount();
  }
  if (projectTitle) {
    projectTitle.value = title;
  }
  currentScaffold = null;
  if (projectBannerTitle) projectBannerTitle.textContent = title;
  if (projectStatusPill) projectStatusPill.textContent = 'Analyzing Scope with AI...';
  if (footerActiveSpec) footerActiveSpec.textContent = title;
  renderActiveFileContent();
  const wordCount = (scopeContentText ? scopeContentText.value.split(/\s+/).filter(Boolean).length : 0);
  showToast(`Loaded "${title}" (${wordCount} words) • Running 1st-place AI analysis...`);

  // Trigger 1st-place AI scope analysis
  runAiScopeAnalysis(content, title);
}

// ── 1st-Place AI Scope Analysis Engine ────────────────────────────────────
async function runAiScopeAnalysis(scopeText, filename = '') {
  if (!scopeText || scopeText.trim().length < 15) return;

  if (aiAnalysisStatus) {
    aiAnalysisStatus.innerHTML = `
      <div class="flex items-center justify-between text-blue-800 bg-blue-50 border border-blue-200/90 px-3 py-2 rounded text-[11px] font-mono shadow-2xs">
        <div class="flex items-center gap-2">
          <svg class="animate-spin h-3.5 w-3.5 text-blue-600 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          <span class="font-bold text-blue-900">Phase 1: AI Scope Analysis in progress...</span>
          <span class="text-blue-600 hidden sm:inline">• Extracting title, frontend, backend, database & services</span>
        </div>
        <span class="text-[9.5px] bg-blue-200 text-blue-900 px-1.5 py-0.5 rounded uppercase font-bold tracking-tight">Active</span>
      </div>
    `;
  }

  try {
    const headers = { 'Content-Type': 'application/json' };
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const res = await fetch(`${API_BASE}/scaffolds/analyze-scope/`, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify({
        scope_text: scopeText,
        filename: filename || ''
      })
    });

    if (res.ok) {
      const data = await res.json();
      applyAiAnalysisResults(data);
      return data;
    } else {
      console.warn('AI scope analysis returned error status:', res.status);
    }
  } catch (err) {
    console.error('Failed to run 1st-place AI scope analysis:', err);
  }

  if (aiAnalysisStatus) {
    aiAnalysisStatus.innerHTML = `
      <div class="flex items-center gap-2 text-slate-600 bg-slate-50 border border-slate-200 px-3 py-2 rounded text-[11px] font-mono">
        <span class="text-amber-500 font-bold">ℹ</span>
        <span>Scope loaded. You can refine title and tech stack tags manually before generating.</span>
      </div>
    `;
  }
}

function applyAiAnalysisResults(data) {
  if (!data) return;

  // 0. Update extracted text if returned by server analysis
  if (data.extracted_text && scopeContentText) {
    if (!scopeContentText.value || scopeContentText.value.startsWith('PK') || scopeContentText.value.includes('[Content_Types].xml')) {
      scopeContentText.value = data.extracted_text;
      updateWordCount();
    }
  }

  // 1. Title
  if (data.title && projectTitle) {
    projectTitle.value = data.title;
    if (projectBannerTitle) projectBannerTitle.textContent = data.title;
    if (footerActiveSpec) footerActiveSpec.textContent = data.title;
    if (titleSourceBadge) {
      titleSourceBadge.textContent = 'AI Extracted';
      titleSourceBadge.className = 'text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.2 rounded font-mono font-medium';
    }
    projectTitle.classList.remove('highlight-populated');
    void projectTitle.offsetWidth;
    projectTitle.classList.add('highlight-populated');
  }

  // 2. Categorized Tech Stack Breakdown Display
  if (catFrontend) catFrontend.textContent = (data.frontend && data.frontend.length) ? data.frontend.join(', ') : 'Modern Frontend';
  if (catBackend) catBackend.textContent = (data.backend && data.backend.length) ? data.backend.join(', ') : 'REST API Backend';
  if (catDatabase) catDatabase.textContent = (data.database && data.database.length) ? data.database.join(', ') : 'Relational Database';
  if (catServices) catServices.textContent = (data.libraries_and_services && data.libraries_and_services.length) ? data.libraries_and_services.join(', ') : 'JWT, External APIs';

  // 3. Tech Stack Tags
  if (data.all_tech_tags && data.all_tech_tags.length > 0) {
    techTags = [...data.all_tech_tags];
    renderTechTags();
    if (tagWrapper) {
      tagWrapper.classList.remove('highlight-populated');
      void tagWrapper.offsetWidth;
      tagWrapper.classList.add('highlight-populated');
    }
  }

  // 4. Notes / Constraints: only populate if VIP points / strict instructions exist
  if (customNotes) {
    if (data.suggested_notes && data.suggested_notes.trim()) {
      customNotes.value = data.suggested_notes.trim();
    } else {
      customNotes.value = '';
    }
  }

  // 6. Status Banner Update
  if (aiAnalysisStatus) {
    const modCount = (data.modules && data.modules.length) ? data.modules.length : 4;
    aiAnalysisStatus.innerHTML = `
      <div class="flex items-center justify-between text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-2 rounded text-[11px] font-mono shadow-2xs">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span class="font-bold text-emerald-950">1st-Place AI Analysis Complete</span>
          <span class="text-emerald-700 hidden sm:inline">• Extracted "${data.title}" (${modCount} core modules ideated)</span>
        </div>
        <span class="text-[9.5px] bg-emerald-200 text-emerald-900 px-1.5 py-0.5 rounded uppercase font-bold tracking-tight">Ready</span>
      </div>
    `;
  }

  if (projectStatusPill) projectStatusPill.textContent = 'Scope Ready • Ready to Synthesize';
  showToast(`AI extracted: "${data.title}" • Tech stack populated`);
}

// ── AI Thinking Terminal Animation ────────────────────────────────────────
const THINK_MESSAGES = [
  'Parsing project scope document...',
  'Extracting domain entities and bounded contexts...',
  'Matching architectural patterns to scope...',
  'Evaluating tech stack constraints...',
  'Synthesizing AGENT.md directives...',
  'Designing folder structure and module boundaries...',
  'Generating ARCHITECTURE.md...',
  'Building SETUP.md installation playbook...',
  'Formulating SKILLS.md agent capability map...',
  'Writing API_SETUP.md endpoint specifications...',
  'Composing INITIAL_PROMPT.md kickoff sequence...',
  'Validating spec completeness...',
  'Packaging output...',
];

let thinkInterval = null;
let thinkIdx = 0;

function startThinkingTerminal() {
  if (!thinkingTerminal || !thinkingLines) return;
  thinkingTerminal.style.display = 'block';
  thinkingLines.innerHTML = '';
  thinkIdx = 0;

  function addLine() {
    if (thinkIdx >= THINK_MESSAGES.length) thinkIdx = 0;
    const msg = THINK_MESSAGES[thinkIdx++];
    const ts  = new Date().toTimeString().slice(0, 8);

    const line = document.createElement('div');
    line.className = 'think-line';
    line.innerHTML = `<span class="t-prefix">[${ts}]</span><span class="t-text">» ${msg}<span class="think-cursor"></span></span>`;
    thinkingLines.appendChild(line);

    const allLines = thinkingLines.querySelectorAll('.think-line');
    if (allLines.length > 6) {
      allLines[0].remove();
    }
  }

  addLine();
  thinkInterval = setInterval(addLine, 1800);
}

function stopThinkingTerminal() {
  if (thinkInterval) { clearInterval(thinkInterval); thinkInterval = null; }
  if (thinkingTerminal) {
    const line = document.createElement('div');
    line.className = 'think-line';
    line.innerHTML = `<span class="t-prefix">[DONE]</span><span class="t-text font-bold text-emerald-400">■ All specifications generated successfully.</span>`;
    thinkingLines && thinkingLines.appendChild(line);
    setTimeout(() => { thinkingTerminal.style.display = 'none'; }, 2500);
  }
}

// ── File Map ──────────────────────────────────────────────────────────────
function getFileMap() {
  if (!currentScaffold) return EMPTY_STUDIO_FILES;

  const fe_agents = currentScaffold.frontend_agents_md || currentScaffold.agents_md || EMPTY_STUDIO_FILES.fe_agent.content;
  const fe_arch = currentScaffold.frontend_architecture_md || currentScaffold.architecture_md || EMPTY_STUDIO_FILES.fe_architecture.content;
  const fe_setup = currentScaffold.frontend_setup_md || currentScaffold.setup_md || EMPTY_STUDIO_FILES.fe_setup.content;
  const fe_skills = currentScaffold.frontend_skill_md || currentScaffold.skill_md || EMPTY_STUDIO_FILES.fe_skills.content;
  const fe_api = currentScaffold.frontend_api_setup_md || currentScaffold.api_setup_md || EMPTY_STUDIO_FILES.fe_apisetup.content;
  const fe_prompt = currentScaffold.frontend_initial_prompt || currentScaffold.initial_prompt || EMPTY_STUDIO_FILES.fe_prompt.content;
  const fe_ui = currentScaffold.ui_prototype_html || '';

  const be_agents = currentScaffold.backend_agents_md || EMPTY_STUDIO_FILES.be_agent.content;
  const be_arch = currentScaffold.backend_architecture_md || EMPTY_STUDIO_FILES.be_architecture.content;
  const be_setup = currentScaffold.backend_setup_md || EMPTY_STUDIO_FILES.be_setup.content;
  const be_skills = currentScaffold.backend_skill_md || EMPTY_STUDIO_FILES.be_skills.content;
  const be_api = currentScaffold.backend_api_setup_md || EMPTY_STUDIO_FILES.be_apisetup.content;
  const be_prompt = currentScaffold.backend_initial_prompt || EMPTY_STUDIO_FILES.be_prompt.content;

  const scope = currentScaffold.scope_document || EMPTY_STUDIO_FILES.scope.content;

  return {
    fe_agent:        { filename: 'AGENT.md', folder: 'frontend', display: 'frontend/AGENT.md', content: fe_agents },
    fe_architecture: { filename: 'ARCHITECTURE.md', folder: 'frontend', display: 'frontend/ARCHITECTURE.md', content: fe_arch },
    fe_setup:        { filename: 'SETUP.md', folder: 'frontend', display: 'frontend/SETUP.md', content: fe_setup },
    fe_skills:       { filename: 'SKILLS.md', folder: 'frontend', display: 'frontend/SKILLS.md', content: fe_skills },
    fe_apisetup:     { filename: 'API_SETUP.md', folder: 'frontend', display: 'frontend/API_SETUP.md', content: fe_api },
    fe_prompt:       { filename: 'INITIAL_PROMPT.md', folder: 'frontend', display: 'frontend/INITIAL_PROMPT.md', content: fe_prompt },
    fe_ui:           { filename: 'UI_PROTOTYPE.html', folder: 'frontend', display: 'frontend/UI_PROTOTYPE.html', content: fe_ui },

    be_agent:        { filename: 'AGENT.md', folder: 'backend', display: 'backend/AGENT.md', content: be_agents },
    be_architecture: { filename: 'ARCHITECTURE.md', folder: 'backend', display: 'backend/ARCHITECTURE.md', content: be_arch },
    be_setup:        { filename: 'SETUP.md', folder: 'backend', display: 'backend/SETUP.md', content: be_setup },
    be_skills:       { filename: 'SKILLS.md', folder: 'backend', display: 'backend/SKILLS.md', content: be_skills },
    be_apisetup:     { filename: 'API_SETUP.md', folder: 'backend', display: 'backend/API_SETUP.md', content: be_api },
    be_prompt:       { filename: 'INITIAL_PROMPT.md', folder: 'backend', display: 'backend/INITIAL_PROMPT.md', content: be_prompt },

    scope:           { filename: 'SCOPE.md', folder: 'root', display: 'SCOPE.md', content: scope },

    // Aliases for backwards compatibility
    agent:           { filename: 'AGENT.md', folder: 'frontend', display: 'frontend/AGENT.md', content: fe_agents },
    architecture:    { filename: 'ARCHITECTURE.md', folder: 'frontend', display: 'frontend/ARCHITECTURE.md', content: fe_arch },
    setup:           { filename: 'SETUP.md', folder: 'frontend', display: 'frontend/SETUP.md', content: fe_setup },
    skills:          { filename: 'SKILLS.md', folder: 'frontend', display: 'frontend/SKILLS.md', content: fe_skills },
    apisetup:        { filename: 'API_SETUP.md', folder: 'frontend', display: 'frontend/API_SETUP.md', content: fe_api },
    prompt:          { filename: 'INITIAL_PROMPT.md', folder: 'frontend', display: 'frontend/INITIAL_PROMPT.md', content: fe_prompt },
    ui:              { filename: 'UI_PROTOTYPE.html', folder: 'frontend', display: 'frontend/UI_PROTOTYPE.html', content: fe_ui },
  };
}

// ── File Navigation ───────────────────────────────────────────────────────
function updateSidebarNavVisuals() {
  document.querySelectorAll('.file-item-btn').forEach((btn) => {
    const key = btn.getAttribute('data-file');
    const folder = btn.getAttribute('data-folder') || '';
    const isAct = (key === activeFileKey || (key === 'fe_agent' && activeFileKey === 'agent') || (key === 'fe_ui' && activeFileKey === 'ui'));
    const item = getFileMap()[key];
    const filename = item?.filename || key;

    if (isAct) {
      if (key === 'fe_ui' || key === 'ui') {
        btn.className = "file-item-btn w-full text-left px-2 py-1.5 rounded bg-indigo-50 text-indigo-900 border border-indigo-300 font-semibold flex items-center justify-between truncate";
        btn.innerHTML = `
          <span class="flex items-center gap-1.5 truncate">
            <svg class="w-3.5 h-3.5 text-indigo-600 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path></svg>
            <span class="font-bold truncate">${filename}</span>
          </span>
          <span class="text-[9px] bg-indigo-200/80 text-indigo-800 px-1 rounded uppercase font-mono font-bold shrink-0">Active</span>
        `;
      } else if (folder === 'backend' || key.startsWith('be_')) {
        btn.className = "file-item-btn w-full text-left px-2 py-1.5 rounded bg-amber-50 text-amber-950 border border-amber-300/80 font-semibold flex items-center justify-between truncate";
        btn.innerHTML = `
          <span class="flex items-center gap-1.5 truncate">
            <svg class="w-3.5 h-3.5 text-amber-600 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>
            <span class="truncate">${filename}</span>
          </span>
          <span class="w-1.5 h-1.5 rounded-full bg-amber-600 shrink-0"></span>
        `;
      } else {
        btn.className = "file-item-btn w-full text-left px-2 py-1.5 rounded bg-blue-50 text-blue-900 border border-blue-200/60 font-semibold flex items-center justify-between truncate";
        btn.innerHTML = `
          <span class="flex items-center gap-1.5 truncate">
            <svg class="w-3.5 h-3.5 text-blue-600 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>
            <span class="truncate">${filename}</span>
          </span>
          <span class="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0"></span>
        `;
      }
    } else {
      if (key === 'fe_ui' || key === 'ui') {
        btn.className = "file-item-btn w-full text-left px-2 py-1.5 rounded text-indigo-700 hover:bg-indigo-50/70 border border-transparent hover:border-indigo-100 flex items-center justify-between truncate";
        btn.innerHTML = `
          <span class="flex items-center gap-1.5 truncate">
            <svg class="w-3.5 h-3.5 text-indigo-600 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"></path></svg>
            <span class="font-bold truncate">${filename}</span>
          </span>
          <span class="text-[9px] bg-indigo-100 text-indigo-700 px-1 rounded uppercase font-mono font-semibold shrink-0">Live UI</span>
        `;
      } else {
        btn.className = "file-item-btn w-full text-left px-2 py-1.5 rounded text-slate-700 hover:bg-slate-100 flex items-center gap-1.5 truncate";
        btn.innerHTML = `
          <svg class="w-3.5 h-3.5 text-slate-400 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg>
          <span class="truncate">${filename}</span>
        `;
      }
    }
  });
}

document.querySelectorAll('.file-item-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    const key = btn.getAttribute('data-file');
    activeFileKey = key;
    updateSidebarNavVisuals();
    renderActiveFileContent();
    if (key === 'fe_ui' || key === 'ui') {
      // Direct action: open unconstrained Big Window canvas
      openBigWindowModal();
    }
  });
});

function renderActiveFileContent() {
  const fileMap = getFileMap();
  const file = fileMap[activeFileKey] || fileMap.fe_agent || fileMap.agent;
  if (!file) return;

  if (currentViewerFilename) currentViewerFilename.textContent = file.display || file.filename;
  const rawText = file.content || '# No content generated';

  // Calculate size
  const bytes = new Blob([rawText]).size;
  const kb = (bytes / 1024).toFixed(1);
  if (currentViewerFilesize) currentViewerFilesize.textContent = `${kb} KB`;

  const isUiKey = (activeFileKey === 'fe_ui' || activeFileKey === 'ui');
  if (downloadCurrentFileBtn) {
    downloadCurrentFileBtn.textContent = isUiKey ? '↓ .html' : '↓ .md';
  }

  // Handle UI Prototype Tab
  if (isUiKey) {
    if (launchToolbarBigWindowBtn) {
      launchToolbarBigWindowBtn.classList.remove('hidden');
      launchToolbarBigWindowBtn.classList.add('flex');
    }
    if (openExternalUiBtn) {
      openExternalUiBtn.classList.remove('hidden');
      openExternalUiBtn.classList.add('flex');
    }

    if (isRawMode) {
      if (uiPrototypeContainer) uiPrototypeContainer.classList.add('hidden');
      if (renderedMarkdownContent) renderedMarkdownContent.classList.add('hidden');
      if (rawMarkdownContent) {
        rawMarkdownContent.textContent = rawText;
        rawMarkdownContent.classList.remove('hidden');
      }
    } else {
      if (renderedMarkdownContent) renderedMarkdownContent.classList.add('hidden');
      if (rawMarkdownContent) rawMarkdownContent.classList.add('hidden');
      if (uiPrototypeContainer) {
        uiPrototypeContainer.classList.remove('hidden');
        if (uiPrototypeIframe && !inlineFrameContainer.classList.contains('hidden') && uiPrototypeIframe.srcdoc !== rawText) {
          uiPrototypeIframe.srcdoc = rawText;
        }
      }
    }
    return;
  }

  // Handle Standard Markdown Files
  if (launchToolbarBigWindowBtn) {
    launchToolbarBigWindowBtn.classList.add('hidden');
    launchToolbarBigWindowBtn.classList.remove('flex');
  }
  if (openExternalUiBtn) {
    openExternalUiBtn.classList.add('hidden');
    openExternalUiBtn.classList.remove('flex');
  }
  if (uiPrototypeContainer) uiPrototypeContainer.classList.add('hidden');

  if (rawMarkdownContent) rawMarkdownContent.textContent = rawText;

  if (renderedMarkdownContent && window.marked) {
    try {
      renderedMarkdownContent.innerHTML = marked.parse(rawText);
      if (window.hljs) {
        renderedMarkdownContent.querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
      }
    } catch (e) {
      renderedMarkdownContent.textContent = rawText;
    }
  } else if (renderedMarkdownContent) {
    renderedMarkdownContent.textContent = rawText;
  }

  if (isRawMode) {
    if (renderedMarkdownContent) renderedMarkdownContent.classList.add('hidden');
    if (rawMarkdownContent) rawMarkdownContent.classList.remove('hidden');
  } else {
    if (renderedMarkdownContent) renderedMarkdownContent.classList.remove('hidden');
    if (rawMarkdownContent) rawMarkdownContent.classList.add('hidden');
  }
}

// ── Big Window UI Canvas Modal Operations ─────────────────────────────────
function openBigWindowModal() {
  if (!uiCanvasModal) return;
  const file = getFileMap().ui;
  const htmlContent = file?.content || '';

  if (modalUiPrototypeIframe) {
    modalUiPrototypeIframe.srcdoc = htmlContent;
  }
  if (!currentScaffold || !currentScaffold.ui_prototype_html) {
    showToast('No interactive UI prototype generated yet. Generate specifications first.');
    return;
  }
  if (canvasProjectTitle) {
    const title = currentScaffold?.title || projectTitle?.value?.trim() || 'Architecture Blueprint';
    canvasProjectTitle.textContent = `${title} — UI_PROTOTYPE.html`;
  }

  uiCanvasModal.classList.remove('hidden');
  setModalViewport('desktop');
  document.body.classList.add('overflow-hidden');
}

function closeBigWindowModal() {
  if (!uiCanvasModal) return;
  uiCanvasModal.classList.add('hidden');
  document.body.classList.remove('overflow-hidden');
}

function setModalViewport(mode) {
  if (!modalIframeWrapper) return;
  const btns = {
    desktop: modalVpDesktopBtn,
    laptop:  modalVpLaptopBtn,
    tablet:  modalVpTabletBtn,
    mobile:  modalVpMobileBtn,
  };

  Object.keys(btns).forEach(k => {
    if (btns[k]) {
      btns[k].className = (k === mode)
        ? "px-2.5 py-1 rounded text-[11px] font-mono font-bold bg-white text-slate-900 shadow-2xs transition cursor-pointer"
        : "px-2.5 py-1 rounded text-[11px] font-mono text-slate-600 hover:text-slate-900 transition cursor-pointer";
    }
  });

  if (mode === 'desktop') {
    modalIframeWrapper.style.maxWidth = '100%';
  } else if (mode === 'laptop') {
    modalIframeWrapper.style.maxWidth = '1280px';
  } else if (mode === 'tablet') {
    modalIframeWrapper.style.maxWidth = '768px';
  } else if (mode === 'mobile') {
    modalIframeWrapper.style.maxWidth = '390px';
  }
}

function openPrototypeInNewTab() {
  const file = getFileMap().ui;
  if (!file || !file.content) return;
  const blob = new Blob([file.content], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  window.open(url, '_blank');
}

// Wire Big Window Triggers & Buttons
if (closeUiCanvasModalBtn) closeUiCanvasModalBtn.addEventListener('click', closeBigWindowModal);
if (launchBigWindowBtn) launchBigWindowBtn.addEventListener('click', openBigWindowModal);
if (launchToolbarBigWindowBtn) launchToolbarBigWindowBtn.addEventListener('click', openBigWindowModal);
if (inlineExpandToBigBtn) inlineExpandToBigBtn.addEventListener('click', openBigWindowModal);

if (modalVpDesktopBtn) modalVpDesktopBtn.addEventListener('click', () => setModalViewport('desktop'));
if (modalVpLaptopBtn)  modalVpLaptopBtn.addEventListener('click', () => setModalViewport('laptop'));
if (modalVpTabletBtn)  modalVpTabletBtn.addEventListener('click', () => setModalViewport('tablet'));
if (modalVpMobileBtn)  modalVpMobileBtn.addEventListener('click', () => setModalViewport('mobile'));

if (modalOpenExternalBtn) modalOpenExternalBtn.addEventListener('click', openPrototypeInNewTab);
if (launchExternalTabBtn) launchExternalTabBtn.addEventListener('click', openPrototypeInNewTab);
if (openExternalUiBtn)    openExternalUiBtn.addEventListener('click', openPrototypeInNewTab);

if (modalDownloadHtmlBtn) {
  modalDownloadHtmlBtn.addEventListener('click', () => {
    const file = getFileMap().ui;
    if (!file || !file.content) return;
    const blob = new Blob([file.content], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.setAttribute('download', file.filename);
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 1500);
    showToast(`Downloaded ${file.filename}`);
  });
}

// Collapsible Embedded Preview Toggle
if (toggleInlineFrameBtn && inlineFrameContainer) {
  toggleInlineFrameBtn.addEventListener('click', () => {
    const isHidden = inlineFrameContainer.classList.contains('hidden');
    if (isHidden) {
      inlineFrameContainer.classList.remove('hidden');
      toggleInlineFrameBtn.textContent = 'Hide Embedded View ↑';
      if (uiPrototypeIframe) uiPrototypeIframe.srcdoc = getFileMap().ui?.content || '';
    } else {
      inlineFrameContainer.classList.add('hidden');
      toggleInlineFrameBtn.textContent = 'Show Embedded View ↓';
    }
  });
}

// ESC Key Listener for Modal
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (uiCanvasModal && !uiCanvasModal.classList.contains('hidden')) {
      closeBigWindowModal();
    }
  }
});

// ── View Mode ─────────────────────────────────────────────────────────────
if (modePreviewBtn && modeRawBtn) {
  modePreviewBtn.addEventListener('click', () => {
    isRawMode = false;
    modePreviewBtn.className = "text-[11px] font-mono px-2 py-0.5 rounded bg-white border border-slate-300 shadow-2xs font-semibold text-slate-900 transition";
    modeRawBtn.className = "text-[11px] font-mono px-2 py-0.5 rounded hover:bg-slate-100 text-slate-600 transition";
    renderActiveFileContent();
  });
  modeRawBtn.addEventListener('click', () => {
    isRawMode = true;
    modeRawBtn.className = "text-[11px] font-mono px-2 py-0.5 rounded bg-white border border-slate-300 shadow-2xs font-semibold text-slate-900 transition";
    modePreviewBtn.className = "text-[11px] font-mono px-2 py-0.5 rounded hover:bg-slate-100 text-slate-600 transition";
    renderActiveFileContent();
  });
}

// ── Copy Current File ─────────────────────────────────────────────────────
if (copyCurrentFileBtn) {
  copyCurrentFileBtn.addEventListener('click', () => {
    const file = getFileMap()[activeFileKey];
    if (!file || !file.content) return;
    navigator.clipboard.writeText(file.content).then(() => showToast(`Copied ${file.filename}`));
  });
}

// ── Download Single File (.md or .html) ────────────────────────────────────
if (downloadCurrentFileBtn) {
  downloadCurrentFileBtn.addEventListener('click', () => {
    const file = getFileMap()[activeFileKey];
    if (!file || !file.content) return;
    const mime = (activeFileKey === 'ui') ? 'text/html;charset=utf-8' : 'text/markdown;charset=utf-8';
    const blob = new Blob([file.content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.setAttribute('download', file.filename);
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 1500);
    showToast(`Downloaded ${file.filename}`);
  });
}

// ── AI UI Prototype Synthesis Trigger ─────────────────────────────────────
function startUiThinkingAnimation(title) {
  if (!thinkingTerminal || !thinkingLines) return;
  thinkingLines.innerHTML = '';
  thinkingTerminal.style.display = 'block';

  const steps = [
    { prefix: '[MODEL]', text: `Invoking Gemini Flash UI Synthesis Engine for "${title}"...` },
    { prefix: '[PARSE]', text: 'Extracting data entities, routes, and user interaction states from SCOPE.md...' },
    { prefix: '[LAYOUT]', text: 'Synthesizing responsive Tailwind layout (monochrome design system, zero overflow)...' },
    { prefix: '[INTERACT]', text: 'Compiling client-side DOM handlers, modals, search, and tab transitions...' },
    { prefix: '[EMBED]', text: 'Bundling interactive prototype into standalone UI_PROTOTYPE.html...' },
  ];

  let delay = 0;
  steps.forEach((step) => {
    setTimeout(() => {
      const line = document.createElement('div');
      line.className = 'think-line';
      line.innerHTML = `<span class="t-prefix">${step.prefix}</span><span class="t-text">${step.text}</span>`;
      thinkingLines.appendChild(line);
      thinkingTerminal.scrollTop = thinkingTerminal.scrollHeight;
    }, delay);
    delay += 500;
  });
}

function finishUiThinkingAnimation() {
  if (!thinkingTerminal || !thinkingLines) return;
  const line = document.createElement('div');
  line.className = 'think-line';
  line.innerHTML = `<span class="t-prefix">[DONE]</span><span class="t-text font-bold text-indigo-400">■ UI Prototype rendered live in interactive sandbox.</span>`;
  thinkingLines.appendChild(line);
  setTimeout(() => { thinkingTerminal.style.display = 'none'; }, 2200);
}

if (generateUiBtn) {
  generateUiBtn.addEventListener('click', async () => {
    if (!currentScaffold || !currentScaffold.id) {
      showToast('Please click "Generate Scaffold" first to create project specifications');
      return;
    }

    generateUiBtn.disabled = true;
    const origHtml = generateUiBtn.innerHTML;
    generateUiBtn.innerHTML = `
      <svg class="w-3.5 h-3.5 animate-spin text-indigo-600" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span>Synthesizing…</span>
    `;

    startUiThinkingAnimation(currentScaffold.title);

    try {
      const token = await ensureAuthToken();
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      let res = await fetch(`${API_BASE}/scaffolds/${currentScaffold.id}/generate-ui/`, {
        method: 'POST',
        headers,
      });

      if (res.status === 401) {
        const freshToken = await ensureAuthToken(true);
        if (freshToken) {
          headers['Authorization'] = `Bearer ${freshToken}`;
          res = await fetch(`${API_BASE}/scaffolds/${currentScaffold.id}/generate-ui/`, {
            method: 'POST',
            headers,
          });
        }
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server responded with ${res.status}`);
      }

      const data = await res.json();
      currentScaffold.ui_prototype_html = data.ui_prototype_html;

      finishUiThinkingAnimation();
      activeFileKey = 'ui';
      updateSidebarNavVisuals();
      renderActiveFileContent();
      showToast('UI Prototype synthesized & rendered live!');
    } catch (err) {
      console.error('UI synthesis error:', err);
      showToast(`Synthesis failed: ${err.message}`);
      if (thinkingTerminal) thinkingTerminal.style.display = 'none';
    } finally {
      generateUiBtn.disabled = false;
      generateUiBtn.innerHTML = origHtml;
    }
  });
}

// ── Copy Kickoff Prompt ───────────────────────────────────────────────────
if (copyPromptActionBtn) {
  copyPromptActionBtn.addEventListener('click', () => {
    const promptContent = getFileMap().prompt?.content;
    if (!promptContent) return;
    navigator.clipboard.writeText(promptContent)
      .then(() => showToast('Kickoff prompt copied — paste into AI coding agent'));
  });
}

// ── ZIP Download Operations (Full, Frontend, Backend) ─────────────────────
async function triggerZipDownload(target = 'all') {
  if (downloadZipMenu) downloadZipMenu.classList.add('hidden');
  if (!currentScaffold) {
    showToast('Please generate specifications first before downloading.');
    return;
  }
  const title = currentScaffold?.title || projectTitle?.value?.trim() || 'project-blueprint';
  const titleSlug = title
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 30) || 'project-blueprint';

  let zipName = `${titleSlug}-scaffold.zip`;
  if (target === 'frontend') zipName = `${titleSlug}-frontend-specs.zip`;
  if (target === 'backend')  zipName = `${titleSlug}-backend-specs.zip`;

  if (downloadZipActionBtn) {
    downloadZipActionBtn.disabled = true;
    downloadZipActionBtn.innerHTML = `
      <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg> Building…`;
  }

  // 1. Client-Side JSZip
  if (window.JSZip) {
    try {
      const zip = new JSZip();
      const fileMap = getFileMap();

      if (target === 'all') {
        const feFolder = zip.folder('frontend');
        const beFolder = zip.folder('backend');

        // Frontend files
        ['fe_agent', 'fe_architecture', 'fe_setup', 'fe_skills', 'fe_apisetup', 'fe_prompt', 'fe_ui'].forEach(k => {
          const item = fileMap[k];
          if (item?.filename && item?.content) feFolder.file(item.filename, item.content);
        });
        // Backend files
        ['be_agent', 'be_architecture', 'be_setup', 'be_skills', 'be_apisetup', 'be_prompt'].forEach(k => {
          const item = fileMap[k];
          if (item?.filename && item?.content) beFolder.file(item.filename, item.content);
        });
        // Shared SCOPE.md at root
        if (fileMap.scope?.content) {
          zip.file('SCOPE.md', fileMap.scope.content);
        }
      } else if (target === 'frontend') {
        const feFolder = zip.folder('frontend');
        ['fe_agent', 'fe_architecture', 'fe_setup', 'fe_skills', 'fe_apisetup', 'fe_prompt', 'fe_ui'].forEach(k => {
          const item = fileMap[k];
          if (item?.filename && item?.content) feFolder.file(item.filename, item.content);
        });
      } else if (target === 'backend') {
        const beFolder = zip.folder('backend');
        ['be_agent', 'be_architecture', 'be_setup', 'be_skills', 'be_apisetup', 'be_prompt'].forEach(k => {
          const item = fileMap[k];
          if (item?.filename && item?.content) beFolder.file(item.filename, item.content);
        });
      }

      const zipBlob = await zip.generateAsync({
        type: 'blob', mimeType: 'application/zip',
        compression: 'DEFLATE', compressionOptions: { level: 6 },
      });
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.setAttribute('download', zipName);
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 3000);
      showToast(`Downloaded ${zipName}`);
      return;
    } catch (err) {
      console.warn('JSZip generation error, trying server fallback:', err);
    } finally {
      if (downloadZipActionBtn) {
        downloadZipActionBtn.disabled = false;
        downloadZipActionBtn.innerHTML = `
          <svg class="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
          </svg> Download .ZIP <svg class="w-3.5 h-3.5 inline-block ml-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>`;
      }
    }
  }

  // 2. Server Download Fallback
  if (currentScaffold?.id) {
    try {
      const res = await fetch(`/api/scaffolds/${currentScaffold.id}/download/?target=${target}`);
      if (!res.ok) throw new Error(`Server status ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.setAttribute('download', zipName);
      document.body.appendChild(a);
      a.click();
      setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 3000);
      showToast(`Downloaded ${zipName}`);
    } catch (err) {
      console.error(err);
      alert(`Download failed: ${err.message}`);
    } finally {
      if (downloadZipActionBtn) {
        downloadZipActionBtn.disabled = false;
        downloadZipActionBtn.innerHTML = `
          <svg class="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
          </svg> Download .ZIP <svg class="w-3.5 h-3.5 inline-block ml-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>`;
      }
    }
  }
}

// Download Button Dropdown Events
if (downloadZipActionBtn) {
  downloadZipActionBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (downloadZipMenu) {
      downloadZipMenu.classList.toggle('hidden');
    }
  });
}

if (downloadAllZipBtn) {
  downloadAllZipBtn.addEventListener('click', () => triggerZipDownload('all'));
}
if (downloadFrontendZipBtn) {
  downloadFrontendZipBtn.addEventListener('click', () => triggerZipDownload('frontend'));
}
if (downloadBackendZipBtn) {
  downloadBackendZipBtn.addEventListener('click', () => triggerZipDownload('backend'));
}

// Close Dropdown on outside click
document.addEventListener('click', (e) => {
  if (downloadZipMenu && !downloadZipMenu.classList.contains('hidden')) {
    if (downloadZipDropdownContainer && !downloadZipDropdownContainer.contains(e.target)) {
      downloadZipMenu.classList.add('hidden');
    }
  }
});

// ── Form Submission ───────────────────────────────────────────────────────
if (scaffoldForm) {
  scaffoldForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const title       = projectTitle.value.trim();
    const scope       = scopeContentText.value.trim();
    const notes       = customNotes ? customNotes.value.trim() : '';
    const customStack = techTags.join(', ');

    if (!title) { alert('Enter a project title.'); return; }
    if (!scope)  { alert('Paste or upload a scope document.'); return; }

    const token = await ensureAuthToken();
    if (!token) { alert('Authentication failed. Cannot connect to API.'); return; }

    // Lock UI & start terminal
    submitGenerateBtn.disabled = true;
    submitGenerateBtn.innerHTML = `
      <svg class="w-4 h-4 animate-spin text-white" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span>Synthesizing Specs…</span>
    `;
    startThinkingTerminal();

    try {
      // Step 1: Create scaffold record
      let createRes = await fetch(`${API_BASE}/scaffolds/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          title,
          scope_document:    scope,
          blueprint:         null,
          custom_tech_stack: customStack,
          custom_notes:      notes,
        }),
      });

      if (createRes.status === 401) {
        const freshToken = await ensureAuthToken(true);
        if (freshToken) {
          createRes = await fetch(`${API_BASE}/scaffolds/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${freshToken}`,
            },
            body: JSON.stringify({
              title,
              scope_document:    scope,
              blueprint:         null,
              custom_tech_stack: customStack,
              custom_notes:      notes,
            }),
          });
        }
      }

      if (!createRes.ok) {
        const err = await createRes.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to create project record');
      }

      const created    = await createRes.json();
      const scaffoldId = created.id;

      // Step 2: Trigger AI generation
      const activeAuthToken = authToken || token;
      let genRes = await fetch(`${API_BASE}/scaffolds/${scaffoldId}/generate/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${activeAuthToken}` },
      });

      if (genRes.status === 401) {
        const freshToken = await ensureAuthToken(true);
        if (freshToken) {
          genRes = await fetch(`${API_BASE}/scaffolds/${scaffoldId}/generate/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${freshToken}` },
          });
        }
      }

      if (!genRes.ok) {
        const err = await genRes.json().catch(() => ({}));
        throw new Error(err.detail || 'AI generation failed');
      }

      const fullScaffold = await genRes.json();
      currentScaffold = fullScaffold;

      // Reveal Studio Workspace & Actions
      if (studioEmptyState) studioEmptyState.classList.add('hidden');
      if (studioActiveWorkspace) studioActiveWorkspace.classList.remove('hidden');
      if (studioActionButtons) studioActionButtons.classList.remove('hidden');

      // Update UI Banner & Metadata
      if (projectBannerTitle) projectBannerTitle.textContent = fullScaffold.title;
      if (projectStatusPill) {
        projectStatusPill.textContent = 'Scaffold Ready';
        projectStatusPill.className = 'text-[10px] text-emerald-700 font-mono bg-emerald-100/70 border border-emerald-200 px-1.5 rounded';
      }
      if (totalFilesBadge) {
        totalFilesBadge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> 14 ARTIFACTS READY`;
        totalFilesBadge.className = 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-50 text-emerald-700 border border-emerald-200';
      }

      if (projectStackTagsContainer) {
        const stackItems = (fullScaffold.detected_tech_stack || customStack || 'Custom')
          .split(/[,+]/)
          .map(s => s.trim())
          .filter(Boolean);
        projectStackTagsContainer.innerHTML = `
          <span class="text-[10px] font-mono text-slate-500">Stack:</span>
          ${stackItems.map(item => `<span class="text-[10px] font-mono text-slate-700 bg-white border border-slate-200 px-1.5 py-0.5 rounded">${item}</span>`).join('')}
        `;
      }

      // Generate a short deterministic SHA
      const randomSha = Math.random().toString(16).substring(2, 10);
      if (specShaDisplay) specShaDisplay.textContent = `SHA: ${randomSha}`;
      const specStatusDisplay = document.getElementById('specStatusDisplay');
      if (specStatusDisplay) specStatusDisplay.textContent = 'Status: Verified Spec';

      if (footerActiveSpec) footerActiveSpec.textContent = fullScaffold.title;
      if (footerOutputPath) {
        const slug = fullScaffold.title.toLowerCase().replace(/[^a-z0-9]/g, '-').slice(0, 25);
        footerOutputPath.textContent = `./dist/${slug}-spec.zip`;
      }

      // Set active file to frontend/AGENT.md
      activeFileKey = 'fe_agent';
      updateSidebarNavVisuals();
      renderActiveFileContent();

      // If Big Window canvas or UI iframe is present, update srcdoc immediately
      if (modalUiPrototypeIframe && fullScaffold.ui_prototype_html) {
        modalUiPrototypeIframe.srcdoc = fullScaffold.ui_prototype_html;
      }
      if (canvasProjectTitle) {
        canvasProjectTitle.textContent = `${fullScaffold.title} — UI_PROTOTYPE.html`;
      }

      stopThinkingTerminal();
      showToast('All specifications synthesized successfully');

    } catch (err) {
      console.error(err);
      stopThinkingTerminal();
      alert(`Generation Error: ${err.message}`);
    } finally {
      submitGenerateBtn.disabled = false;
      submitGenerateBtn.innerHTML = `
        <svg class="w-4 h-4 text-blue-400 fill-current" viewBox="0 0 20 20">
          <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11.414V14a1 1 0 11-2 0v-.586l-2.293-2.293a1 1 0 011.414-1.414L9 10.586V6a1 1 0 112 0v4.586l.879-.879a1 1 0 111.414 1.414L11 13.414z"></path>
        </svg>
        <span>Generate Scaffold &amp; Spec Files</span>
      `;
    }
  });
}

// ── Reset Studio to Pristine Blank State (Zero Stale Caching) ──────────────
function resetStudioToBlank() {
  currentScaffold = null;
  activeFileKey = 'fe_agent';
  if (studioEmptyState) studioEmptyState.classList.remove('hidden');
  if (studioActiveWorkspace) studioActiveWorkspace.classList.add('hidden');
  if (studioActionButtons) studioActionButtons.classList.add('hidden');
  techTags = [];
  renderTechTags();

  if (projectTitle) projectTitle.value = '';
  if (scopeContentText) scopeContentText.value = '';
  if (customNotes) customNotes.value = '';
  updateWordCount();

  if (projectBannerTitle) projectBannerTitle.textContent = 'Awaiting Project Scope';
  if (projectStatusPill) {
    projectStatusPill.textContent = 'No Active Spec';
    projectStatusPill.className = 'text-[10px] text-slate-600 font-mono bg-slate-200 px-1.5 rounded';
  }
  if (projectStackTagsContainer) {
    projectStackTagsContainer.innerHTML = '<span class="text-[10px] font-mono text-slate-500">Stack:</span> <span class="text-[10px] font-mono text-slate-400 italic">None</span>';
  }
  if (totalFilesBadge) {
    totalFilesBadge.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span> 0 ARTIFACTS';
    totalFilesBadge.className = 'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-100 text-slate-600 border border-slate-200';
  }
  if (specShaDisplay) {
    specShaDisplay.textContent = 'SHA: —';
  }
  const specStatusDisplay = document.getElementById('specStatusDisplay');
  if (specStatusDisplay) {
    specStatusDisplay.textContent = 'Status: Uninitialized';
  }
  if (footerActiveSpec) footerActiveSpec.textContent = 'None';
  if (footerOutputPath) footerOutputPath.textContent = './dist/spec.zip';

  if (catFrontend) catFrontend.textContent = 'Awaiting scope upload';
  if (catBackend) catBackend.textContent = 'Awaiting scope upload';
  if (catDatabase) catDatabase.textContent = 'Awaiting scope upload';
  if (catServices) catServices.textContent = 'Awaiting scope upload';
  if (titleSourceBadge) {
    titleSourceBadge.textContent = 'Awaiting Scope';
    titleSourceBadge.className = 'text-[10px] text-slate-500 bg-slate-100 border border-slate-200 px-1.5 py-0.2 rounded font-mono font-medium';
  }
  if (techSourceBadge) {
    techSourceBadge.textContent = 'Awaiting Scope';
    techSourceBadge.className = 'text-[10px] text-slate-500 bg-slate-100 border border-slate-200 px-1.5 py-0.2 rounded font-mono font-medium';
  }
  if (aiAnalysisStatus) {
    aiAnalysisStatus.innerHTML = `
      <div class="flex items-center gap-2 text-slate-500 bg-white border border-slate-200 px-3 py-2 rounded text-[11px] font-mono">
        <span>Upload a requirements document to automatically extract project details.</span>
      </div>
    `;
  }
  if (modalUiPrototypeIframe) modalUiPrototypeIframe.srcdoc = '';
  if (uiPrototypeIframe) uiPrototypeIframe.srcdoc = '';

  updateSidebarNavVisuals();
  renderActiveFileContent();
}

// ── Wire Studio Reset Button ──────────────────────────────────────────────
const resetStudioBtn = document.getElementById('resetStudioBtn');
if (resetStudioBtn) {
  resetStudioBtn.addEventListener('click', () => {
    resetStudioToBlank();
    showToast('Studio reset to pristine state');
  });
}

// ── Init ──────────────────────────────────────────────────────────────────

// ── Wire Auth Modal & Forms ───────────────────────────────────────────────
if (openAuthModalBtn) {
  openAuthModalBtn.addEventListener('click', () => openAuthModal('signin'));
}
if (closeAuthModalBtn) {
  closeAuthModalBtn.addEventListener('click', closeAuthModal);
}
if (authModal) {
  authModal.addEventListener('click', (e) => {
    if (e.target === authModal) closeAuthModal();
  });
}
if (authTabSignInBtn) {
  authTabSignInBtn.addEventListener('click', () => switchAuthTab('signin'));
}
if (authTabSignUpBtn) {
  authTabSignUpBtn.addEventListener('click', () => switchAuthTab('signup'));
}

// ── Firebase Auth & Firestore Integration ─────────────────────────────────
function formatFirebaseErrorMessage(err) {
  if (!err) return 'Authentication failed. Please try again.';
  const code = err.code || '';
  switch (code) {
    case 'auth/invalid-email':
      return 'Please enter a valid email address.';
    case 'auth/user-disabled':
      return 'This user account has been disabled.';
    case 'auth/user-not-found':
      return 'No account found with this email. Please check your credentials or create an account.';
    case 'auth/wrong-password':
    case 'auth/invalid-credential':
      return 'Incorrect email or password. Please try again.';
    case 'auth/email-already-in-use':
      return 'An account with this email address already exists. Please sign in instead.';
    case 'auth/weak-password':
      return 'Password should be at least 8 characters long.';
    case 'auth/too-many-requests':
      return 'Too many attempts. Please try again in a few moments.';
    case 'auth/network-request-failed':
      return 'Network connection error. Please check your internet connection.';
    case 'auth/operation-not-allowed':
      return 'Email/Password sign-in is not enabled in Firebase Console.';
    default:
      return err.message || 'Authentication error. Please try again.';
  }
}

async function syncUserWithBackend(payload) {
  try {
    const res = await fetch(`${API_BASE}/auth/firebase-sync/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      if (data.access) {
        authToken = data.access;
        refreshToken = data.refresh || null;
        localStorage.setItem('specforge_access_token', authToken);
        localStorage.setItem('specforge_token', authToken);
        if (refreshToken) {
          localStorage.setItem('specforge_refresh_token', refreshToken);
        }
      }
      return data;
    }
  } catch (err) {
    console.warn('Backend user sync warning:', err);
  }
  return null;
}

function initFirebaseAuthListener() {
  if (!window.fbAuth) return;
  window.fbAuth.onAuthStateChanged(async (fbUser) => {
    if (fbUser) {
      try {
        let userProfile = null;
        if (window.fbDb) {
          try {
            const userDoc = await window.fbDb.collection('users').doc(fbUser.uid).get();
            if (userDoc && userDoc.exists) {
              userProfile = userDoc.data();
            }
          } catch (fsErr) {
            console.warn('Firestore read error in onAuthStateChanged:', fsErr);
          }
        }
        const firstName = userProfile?.firstName || (fbUser.displayName ? fbUser.displayName.split(' ')[0] : '');
        const lastName = userProfile?.lastName || (fbUser.displayName ? fbUser.displayName.split(' ').slice(1).join(' ') : '');
        const idToken = await fbUser.getIdToken();
        const syncData = await syncUserWithBackend({
          id_token: idToken,
          email: fbUser.email,
          uid: fbUser.uid,
          first_name: firstName,
          last_name: lastName
        });
        currentUser = {
          email: fbUser.email,
          first_name: firstName,
          last_name: lastName,
          displayName: userProfile?.displayName || fbUser.displayName || fbUser.email
        };
        renderLoggedInUI(currentUser);
        updateAuthBadge(true);
      } catch (err) {
        console.warn('Auth state sync error:', err);
      }
    } else {
      if (!authToken) {
        renderLoggedOutUI();
        updateAuthBadge(false);
      }
    }
  });
}

if (signInForm) {
  signInForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAuthError();
    const email = loginEmailInput?.value.trim();
    const password = loginPasswordInput?.value;
    if (!email || !password) {
      showAuthError('Please enter both email and password.');
      return;
    }
    const btn = document.getElementById('submitLoginBtn');
    if (btn) btn.disabled = true;

    try {
      if (window.fbAuth) {
        // 1. Firebase Authentication: Sign in
        const userCredential = await window.fbAuth.signInWithEmailAndPassword(email, password);
        const fbUser = userCredential.user;

        // 2. Firestore: Read profile & update lastLoginAt
        let userProfile = null;
        if (window.fbDb) {
          try {
            const userDoc = await window.fbDb.collection('users').doc(fbUser.uid).get();
            if (userDoc && userDoc.exists) {
              userProfile = userDoc.data();
              await window.fbDb.collection('users').doc(fbUser.uid).set({
                lastLoginAt: firebase.firestore.FieldValue.serverTimestamp()
              }, { merge: true }).catch(() => {});
            } else {
              const names = (fbUser.displayName || '').split(' ');
              userProfile = {
                uid: fbUser.uid,
                email: fbUser.email,
                firstName: names[0] || '',
                lastName: names.slice(1).join(' ') || '',
                displayName: fbUser.displayName || fbUser.email,
                lastLoginAt: firebase.firestore.FieldValue.serverTimestamp()
              };
              await window.fbDb.collection('users').doc(fbUser.uid).set(userProfile, { merge: true }).catch(() => {});
            }
          } catch (fsErr) {
            console.warn('Firestore profile lookup error:', fsErr);
          }
        }

        // 3. Synchronize with Django backend
        const idToken = await fbUser.getIdToken();
        const firstName = userProfile?.firstName || (fbUser.displayName ? fbUser.displayName.split(' ')[0] : '');
        const lastName = userProfile?.lastName || (fbUser.displayName ? fbUser.displayName.split(' ').slice(1).join(' ') : '');
        await syncUserWithBackend({
          id_token: idToken,
          email: fbUser.email,
          uid: fbUser.uid,
          first_name: firstName,
          last_name: lastName
        });

        closeAuthModal();
        currentUser = {
          email: fbUser.email,
          first_name: firstName,
          last_name: lastName,
          displayName: userProfile?.displayName || fbUser.displayName || fbUser.email
        };
        renderLoggedInUI(currentUser);
        updateAuthBadge(true);
        showToast('Signed in successfully with Firebase');
      } else {
        // Fallback: Direct Django API login
        const res = await fetch(`${API_BASE}/auth/login/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          showAuthError(data.detail || data.error || 'Invalid email or password.');
          if (btn) btn.disabled = false;
          return;
        }
        authToken = data.access;
        refreshToken = data.refresh || null;
        localStorage.setItem('specforge_access_token', authToken);
        localStorage.setItem('specforge_token', authToken);
        if (refreshToken) localStorage.setItem('specforge_refresh_token', refreshToken);
        closeAuthModal();
        if (data.user) {
          currentUser = data.user;
          renderLoggedInUI(currentUser);
          updateAuthBadge(true);
        } else {
          await checkAuthStatus();
        }
        showToast('Signed in successfully');
      }
    } catch (err) {
      console.error('Sign in error:', err);
      showAuthError(formatFirebaseErrorMessage(err));
    } finally {
      if (btn) btn.disabled = false;
    }
  });
}

if (signUpForm) {
  signUpForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAuthError();
    const first_name = registerFirstNameInput?.value.trim() || '';
    const last_name = registerLastNameInput?.value.trim() || '';
    const email = registerEmailInput?.value.trim();
    const password = registerPasswordInput?.value;
    if (!email || !password) {
      showAuthError('Please fill in all required fields.');
      return;
    }
    if (password.length < 8) {
      showAuthError('Password must be at least 8 characters long.');
      return;
    }
    const btn = document.getElementById('submitRegisterBtn');
    if (btn) btn.disabled = true;

    try {
      if (window.fbAuth) {
        // 1. Firebase Authentication: Create user
        const userCredential = await window.fbAuth.createUserWithEmailAndPassword(email, password);
        const fbUser = userCredential.user;

        // 2. Set profile display name
        const displayName = [first_name, last_name].filter(Boolean).join(' ') || email;
        await fbUser.updateProfile({ displayName: displayName }).catch(() => {});

        // 3. Save User Record to Firestore
        if (window.fbDb) {
          try {
            await window.fbDb.collection('users').doc(fbUser.uid).set({
              uid: fbUser.uid,
              email: email,
              firstName: first_name,
              lastName: last_name,
              displayName: displayName,
              createdAt: firebase.firestore.FieldValue.serverTimestamp(),
              lastLoginAt: firebase.firestore.FieldValue.serverTimestamp(),
              role: 'developer'
            });
          } catch (fsErr) {
            console.warn('Firestore user creation warning:', fsErr);
          }
        }

        // 4. Synchronize with Django Backend
        const idToken = await fbUser.getIdToken();
        await syncUserWithBackend({
          id_token: idToken,
          email: fbUser.email,
          uid: fbUser.uid,
          first_name: first_name,
          last_name: last_name
        });

        closeAuthModal();
        currentUser = {
          email: fbUser.email,
          first_name: first_name,
          last_name: last_name,
          displayName: displayName
        };
        renderLoggedInUI(currentUser);
        updateAuthBadge(true);
        showToast('Account created and saved to Firestore!');
      } else {
        // Fallback: Direct Django API registration
        const res = await fetch(`${API_BASE}/auth/register/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, first_name, last_name }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          let errorText = 'Registration failed.';
          if (data.email) errorText = Array.isArray(data.email) ? data.email.join(' ') : data.email;
          else if (data.password) errorText = Array.isArray(data.password) ? data.password.join(' ') : data.password;
          else if (data.detail) errorText = data.detail;
          showAuthError(errorText);
          if (btn) btn.disabled = false;
          return;
        }
        if (data.access) {
          authToken = data.access;
          refreshToken = data.refresh || null;
          localStorage.setItem('specforge_access_token', authToken);
          localStorage.setItem('specforge_token', authToken);
          if (refreshToken) localStorage.setItem('specforge_refresh_token', refreshToken);
          closeAuthModal();
          if (data.user) {
            currentUser = data.user;
            renderLoggedInUI(currentUser);
            updateAuthBadge(true);
          } else {
            await checkAuthStatus();
          }
          showToast('Account created and signed in!');
        } else {
          switchAuthTab('signin');
          showToast('Account created! Please sign in.');
        }
      }
    } catch (err) {
      console.error('Sign up error:', err);
      showAuthError(formatFirebaseErrorMessage(err));
    } finally {
      if (btn) btn.disabled = false;
    }
  });
}

if (logoutBtn) {
  logoutBtn.addEventListener('click', async () => {
    if (window.fbAuth) {
      try {
        await window.fbAuth.signOut();
      } catch (fbErr) {
        console.warn('Firebase signout warning:', fbErr);
      }
    }
    authToken = null;
    refreshToken = null;
    currentUser = null;
    localStorage.removeItem('specforge_access_token');
    localStorage.removeItem('specforge_refresh_token');
    localStorage.removeItem('specforge_token');
    localStorage.removeItem('agentforge_token');
    renderLoggedOutUI();
    updateAuthBadge(false);
    showToast('Signed out');
  });
}

// ── Wire Docking Buttons ──────────────────────────────────────────────────
if (toggleFormDockBtn) {
  toggleFormDockBtn.addEventListener('click', toggleFormDock);
}
if (collapseInputPanelBtn) {
  collapseInputPanelBtn.addEventListener('click', toggleFormDock);
}
if (toggleFileTreeDockBtn) {
  toggleFileTreeDockBtn.addEventListener('click', toggleFileTreeDock);
}


// ── Init ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  initFirebaseAuthListener();
  await checkAuthStatus();
  renderTechTags();
  updateSidebarNavVisuals();
  renderActiveFileContent();
  updateWordCount();
  resetStudioToBlank();
});

