import { AuthController } from './auth.js';
import { ActiveFilters, FilterOptions, KPIScorecard, ParetoItem, GridRecord } from './types.js';

class DashboardApp {
  private authController: AuthController;
  private apiBaseUrl: string = (typeof window !== 'undefined' && window.location.origin && !window.location.origin.startsWith('file')) ? window.location.origin : 'http://127.0.0.1:5000';

  private activeFilters: ActiveFilters = {
    months: [],
    month: '',
    mtm_types: ['KA'],
    mtm_type: 'KA',
    branches: [],
    mtm_aliases: [],
    brand_groups: [],
    items: [],
    metric_type: 'idr'
  };
  private activeParetoDimension: string = 'alasan';

  constructor() {
    this.authController = new AuthController();
    this.initDOM();
    this.setupCustomSelectListeners();
    this.setupEventListeners();
    this.checkAuthenticationGate();
  }

  private initDOM(): void {
    console.log('Initializing MTM Dashboard App...');
  }

  private checkAuthenticationGate(): void {
    const gateView = document.getElementById('loginGateView');
    const appContent = document.getElementById('appDashboardContent');

    if (gateView) gateView.style.display = 'none';
    if (appContent) appContent.style.display = 'block';

    const btnUpload = document.getElementById('btnOpenUploadModal');
    if (btnUpload) btnUpload.style.display = 'inline-flex';

    this.updateUserUI();
    this.loadFilterOptions();
  }



  private setupCustomSelectListeners(): void {
    document.querySelectorAll('.custom-select-container').forEach(container => {
      const trigger = container.querySelector('.custom-select-trigger');
      const searchInput = container.querySelector('.custom-search-input') as HTMLInputElement;

      trigger?.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = container.classList.contains('open');
        document.querySelectorAll('.custom-select-container.open').forEach(c => c.classList.remove('open'));
        
        if (!isOpen) {
          container.classList.add('open');
          if (searchInput) {
            searchInput.value = '';
            const optionsList = container.querySelector('.custom-options-list');
            if (optionsList) {
              Array.from(optionsList.querySelectorAll('.custom-option')).forEach(opt => (opt as HTMLElement).style.display = '');
            }
            setTimeout(() => searchInput.focus(), 50);
          }
        }
      });

      searchInput?.addEventListener('input', (e) => {
        const kw = (((e.target as HTMLInputElement).value) || '').toLowerCase().trim();
        const optionsList = container.querySelector('.custom-options-list');
        if (!optionsList) return;
        Array.from(optionsList.querySelectorAll('.custom-option')).forEach(opt => {
          const txt = opt.textContent?.toLowerCase() || '';
          (opt as HTMLElement).style.display = txt.includes(kw) ? '' : 'none';
        });
      });
    });

    document.addEventListener('click', () => {
      document.querySelectorAll('.custom-select-container.open').forEach(c => c.classList.remove('open'));
    });
  }

  private setupEventListeners(): void {
    // Mandatory Gate Login Form
    const loginFormGate = document.getElementById('loginFormGate');
    loginFormGate?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const userVal = (document.getElementById('usernameInputGate') as HTMLInputElement).value;
      const passVal = (document.getElementById('passwordInputGate') as HTMLInputElement).value;
      const errBox = document.getElementById('loginGateError');

      try {
        if (errBox) errBox.style.display = 'none';
        await this.authController.login(userVal, passVal, this.apiBaseUrl);
        this.checkAuthenticationGate();
      } catch (err: any) {
        if (errBox) {
          errBox.textContent = err.message || 'Login gagal. Periksa username dan password.';
          errBox.style.display = 'block';
        }
      }
    });

    // Logout Trigger
    const btnLoginLogout = document.getElementById('btnLoginLogout');
    btnLoginLogout?.addEventListener('click', () => {
      this.authController.clearSession();
      this.checkAuthenticationGate();
    });

    // Metric Switcher Toggle
    const btnIDR = document.getElementById('btnMetricIDR');
    const btnQty = document.getElementById('btnMetricQty');
    btnIDR?.addEventListener('click', () => {
      this.activeFilters.metric_type = 'idr';
      btnIDR.classList.add('active');
      btnQty?.classList.remove('active');
      this.refreshDashboardData();
    });
    btnQty?.addEventListener('click', () => {
      this.activeFilters.metric_type = 'qty';
      btnQty.classList.add('active');
      btnIDR?.classList.remove('active');
      this.refreshDashboardData();
    });

    // Reset Filters
    document.getElementById('btnResetFilter')?.addEventListener('click', () => {
      this.activeFilters.months = [];
      this.activeFilters.month = '';
      this.activeFilters.mtm_types = ['KA'];
      this.activeFilters.mtm_type = 'KA';
      this.activeFilters.branches = [];
      this.activeFilters.mtm_aliases = [];
      this.activeFilters.brand_groups = [];
      this.activeFilters.items = [];
      delete this.activeFilters.reason;

      document.querySelectorAll('.custom-option-checkbox').forEach(cb => (cb as HTMLInputElement).checked = false);

      const resetMap: Record<string, string> = {
        'filterMonth': 'Semua Bulan (All Months)',
        'filterMTMType': 'KA',
        'filterBranch': 'Semua Cabang',
        'filterAlias': 'Semua Alias',
        'filterBrandGroup': 'Semua Grup Brand',
        'filterItem': 'Semua Produk / Item'
      };

      Object.entries(resetMap).forEach(([id, text]) => {
        const select = document.getElementById(id) as HTMLSelectElement;
        const container = select?.closest('.custom-select-container');
        if (container) {
          const txtEl = container.querySelector('.custom-select-text');
          if (txtEl) txtEl.textContent = text;
        }
      });

      this.refreshDashboardData();
    });

    // Pareto Tabs
    const tabs = document.querySelectorAll('.pareto-tab');
    tabs.forEach(t => {
      t.addEventListener('click', (e) => {
        tabs.forEach(x => x.classList.remove('active'));
        const target = e.target as HTMLElement;
        target.classList.add('active');
        this.activeParetoDimension = target.getAttribute('data-dim') || 'alasan';
        this.fetchParetoData();
      });
    });

    // PPT Export Modal
    const exportModal = document.getElementById('exportModal');
    const btnOpenExport = document.getElementById('btnOpenExportModal');
    const btnCloseExport = document.getElementById('btnCloseExportModal');
    const exportForm = document.getElementById('exportForm');

    btnOpenExport?.addEventListener('click', () => {
      if (exportModal) exportModal.style.display = 'flex';
    });

    btnCloseExport?.addEventListener('click', () => {
      if (exportModal) exportModal.style.display = 'none';
    });

    exportForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btnConfirm = document.getElementById('btnConfirmExport') as HTMLButtonElement;
      if (btnConfirm) {
        btnConfirm.disabled = true;
        btnConfirm.textContent = 'Mengekspor Slide PPT...';
      }

      try {
        const payload = {
          ...this.activeFilters,
          selected_modules: {
            kpi_summary: (document.getElementById('chkKpiSummary') as HTMLInputElement).checked,
            pareto_sheets: (document.getElementById('chkParetoSheets') as HTMLInputElement).checked,
            detail_grid: (document.getElementById('chkDetailGrid') as HTMLInputElement).checked
          }
        };

        const res = await fetch(`${this.apiBaseUrl}/api/export/ppt`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Gagal mengunduh file PPT.');

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Laporan_Service_Level_MTM_${this.activeFilters.month || 'Summary'}.pptx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        if (exportModal) exportModal.style.display = 'none';
      } catch (err: any) {
        alert(err.message || 'Gagal ekspor PPT.');
      } finally {
        if (btnConfirm) {
          btnConfirm.disabled = false;
          btnConfirm.textContent = 'Unduh Laporan PPT';
        }
      }
    });

    // Upload Dataset Modal
    const uploadModal = document.getElementById('uploadModal');
    const btnOpenUpload = document.getElementById('btnOpenUploadModal');
    const btnCloseUpload = document.getElementById('btnCloseUploadModal');
    const uploadForm = document.getElementById('uploadForm');

    btnOpenUpload?.addEventListener('click', () => {
      if (uploadModal) uploadModal.style.display = 'flex';
    });

    btnCloseUpload?.addEventListener('click', () => {
      if (uploadModal) uploadModal.style.display = 'none';
    });

    uploadForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fileInput = document.getElementById('datasetFileInput') as HTMLInputElement;
      const progressMsg = document.getElementById('uploadProgressMsg');
      const btnConfirm = document.getElementById('btnConfirmUpload') as HTMLButtonElement;

      if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        alert('Silakan pilih file Excel (.xlsx) terlebih dahulu.');
        return;
      }

      const file = fileInput.files[0];
      if (btnConfirm) {
        btnConfirm.disabled = true;
        btnConfirm.textContent = 'Mengunggah File...';
      }
      if (progressMsg) progressMsg.style.display = 'block';

      try {
        const fileBytes = await file.arrayBuffer();
        const res = await fetch(`${this.apiBaseUrl}/api/data/upload`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/octet-stream' },
          body: fileBytes
        });

        const json = await res.json();
        if (res.ok && json.status === 'success') {
          alert('Berhasil! Dataset Excel telah diunggah dan database SQLite berhasil diindeks ulang.');
          if (uploadModal) uploadModal.style.display = 'none';
          this.loadFilterOptions();
        } else {
          throw new Error(json.message || 'Gagal mengunggah file.');
        }
      } catch (err: any) {
        alert(err.message || 'Gagal mengunggah file Excel.');
      } finally {
        if (btnConfirm) {
          btnConfirm.disabled = false;
          btnConfirm.textContent = 'Unggah & Rebuild Data';
        }
        if (progressMsg) progressMsg.style.display = 'none';
      }
    });
  }

  private updateUserUI(): void {
    const user = this.authController.getCurrentUser();
    const badge = document.getElementById('userRoleBadge');
    const btn = document.getElementById('btnLoginLogout');
    const btnUpload = document.getElementById('btnOpenUploadModal');

    if (user) {
      if (badge) {
        badge.textContent = `${user.role.toUpperCase()}: ${user.username}`;
        badge.className = `role-badge ${user.role}`;
      }
      if (btn) btn.textContent = 'Logout';
      if (btnUpload) btnUpload.style.display = user.can_upload ? 'inline-flex' : 'none';
    } else {
      if (badge) {
        badge.textContent = 'GUEST';
        badge.className = 'role-badge user';
      }
      if (btn) btn.textContent = 'Login';
      if (btnUpload) btnUpload.style.display = 'none';
    }
  }

  private async loadFilterOptions(): Promise<void> {
    try {
      const res = await fetch(`${this.apiBaseUrl}/api/data/filters`);
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        const opts: FilterOptions = json.data;
        this.populateDropdown('filterMonth', opts.months, opts.latest_month);
        this.populateDropdown('filterMTMType', opts.mtm_types, opts.default_mtm_type);
        this.populateDropdown('filterBranch', opts.branches);
        this.populateDropdown('filterAlias', opts.mtm_aliases);
        this.populateDropdown('filterBrandGroup', opts.brand_groups);
        this.populateDropdown('filterItem', opts.items);

        this.activeFilters.months = [opts.latest_month];
        this.activeFilters.month = opts.latest_month;
        this.activeFilters.mtm_types = [opts.default_mtm_type];
        this.activeFilters.mtm_type = opts.default_mtm_type;
        this.refreshDashboardData();
      }
    } catch (e) {
      console.warn('Backend API filter fetch fallback active');
      this.refreshDashboardData();
    }
  }

  private async updateCascadingDropdowns(): Promise<void> {
    try {
      const res = await fetch(`${this.apiBaseUrl}/api/data/filters`);
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        const opts: FilterOptions = json.data;
        if (!this.activeFilters.branches || this.activeFilters.branches.length === 0) {
          this.populateDropdown('filterBranch', opts.branches);
        }
        if (!this.activeFilters.mtm_aliases || this.activeFilters.mtm_aliases.length === 0) {
          this.populateDropdown('filterAlias', opts.mtm_aliases);
        }
        if (!this.activeFilters.brand_groups || this.activeFilters.brand_groups.length === 0) {
          this.populateDropdown('filterBrandGroup', opts.brand_groups);
        }
        if (!this.activeFilters.items || this.activeFilters.items.length === 0) {
          this.populateDropdown('filterItem', opts.items);
        }
      }
    } catch (e) {
      console.warn('Cascading dropdown update error', e);
    }
  }

  private populateDropdown(id: string, items: string[], defaultVal?: string): void {
    const select = document.getElementById(id) as HTMLSelectElement;
    if (!select) return;

    select.innerHTML = '';
    const container = select.closest('.custom-select-container');
    const textEl = container?.querySelector('.custom-select-text');
    const optionsList = container?.querySelector('.custom-options-list');

    if (!optionsList) return;
    optionsList.innerHTML = '';

    const labelMap: Record<string, string> = {
      'filterMonth': 'Pilih Bulan',
      'filterMTMType': 'Semua Jenis MTM',
      'filterBranch': 'Semua Cabang',
      'filterAlias': 'Semua Alias',
      'filterBrandGroup': 'Semua Grup Brand',
      'filterItem': 'Semua Produk / Item'
    };

    const keyMap: Record<string, keyof ActiveFilters> = {
      'filterMonth': 'months',
      'filterMTMType': 'mtm_types',
      'filterBranch': 'branches',
      'filterAlias': 'mtm_aliases',
      'filterBrandGroup': 'brand_groups',
      'filterItem': 'items'
    };

    const targetKey = keyMap[id];
    let selectedValues = (this.activeFilters[targetKey] as string[]) || [];
    if (defaultVal && selectedValues.length === 0 && (id === 'filterMonth' || id === 'filterMTMType')) {
      selectedValues = [defaultVal];
      (this.activeFilters[targetKey] as string[]) = selectedValues;
      if (id === 'filterMonth') this.activeFilters.month = defaultVal;
      if (id === 'filterMTMType') this.activeFilters.mtm_type = defaultVal;
    }

    const isSingleMonth = (id === 'filterMonth');

    const updateDisplayAndFilters = () => {
      if (isSingleMonth) return;
      const checkedBoxes = Array.from(optionsList.querySelectorAll('.custom-option-checkbox:checked')) as HTMLInputElement[];
      const checkedVals = checkedBoxes.map(cb => cb.value);
      (this.activeFilters[targetKey] as string[]) = checkedVals;

      if (id === 'filterMTMType') {
        this.activeFilters.mtm_type = checkedVals.length === 1 ? checkedVals[0] : (checkedVals.length > 1 ? 'ALL' : '');
      }

      if (textEl) {
        if (checkedVals.length === 0) {
          textEl.textContent = labelMap[id];
        } else if (checkedVals.length === 1) {
          textEl.textContent = checkedVals[0];
        } else {
          textEl.textContent = `${checkedVals.length} Terpilih`;
        }
      }
      this.refreshDashboardData();
    };

    if (!isSingleMonth) {
      const actionsBar = document.createElement('div');
      actionsBar.className = 'custom-actions-bar';
      actionsBar.innerHTML = `
        <span class="custom-action-link act-select-all">✓ Pilih Semua</span>
        <span class="custom-action-link act-clear">✕ Bersihkan</span>
      `;
      optionsList.appendChild(actionsBar);

      actionsBar.querySelector('.act-select-all')?.addEventListener('click', (e) => {
        e.stopPropagation();
        optionsList.querySelectorAll('.custom-option-checkbox').forEach(cb => (cb as HTMLInputElement).checked = true);
        updateDisplayAndFilters();
      });

      actionsBar.querySelector('.act-clear')?.addEventListener('click', (e) => {
        e.stopPropagation();
        optionsList.querySelectorAll('.custom-option-checkbox').forEach(cb => (cb as HTMLInputElement).checked = false);
        updateDisplayAndFilters();
      });
    }

    const monthItems = isSingleMonth ? ['Semua Bulan', ...(items || [])] : (items || []);

    monthItems.forEach(it => {
      const opt = document.createElement('option');
      opt.value = (it === 'Semua Bulan') ? 'ALL' : it;
      opt.textContent = it;
      if (selectedValues.includes(it) || (it === 'Semua Bulan' && selectedValues.length === 0)) opt.selected = true;
      select.appendChild(opt);

      const divOpt = document.createElement('div');
      divOpt.className = 'custom-option';
      
      if (isSingleMonth) {
        if (selectedValues.includes(it) || (it === 'Semua Bulan' && selectedValues.length === 0)) divOpt.classList.add('selected');
        const span = document.createElement('span');
        span.textContent = it;
        divOpt.appendChild(span);

        divOpt.addEventListener('click', (e) => {
          e.stopPropagation();
          optionsList.querySelectorAll('.custom-option').forEach(o => o.classList.remove('selected'));
          divOpt.classList.add('selected');

          if (it === 'Semua Bulan') {
            this.activeFilters.months = [];
            this.activeFilters.month = 'ALL';
            if (textEl) textEl.textContent = 'Semua Bulan';
          } else {
            this.activeFilters.months = [it];
            this.activeFilters.month = it;
            if (textEl) textEl.textContent = it;
          }
          container?.classList.remove('open');
          this.refreshDashboardData();
        });
      } else {
        const chk = document.createElement('input');
        chk.type = 'checkbox';
        chk.className = 'custom-option-checkbox';
        chk.value = it;
        chk.checked = selectedValues.includes(it);

        const span = document.createElement('span');
        span.textContent = it;

        divOpt.appendChild(chk);
        divOpt.appendChild(span);

        divOpt.addEventListener('click', (e) => {
          e.stopPropagation();
          if (e.target !== chk) chk.checked = !chk.checked;
          updateDisplayAndFilters();
        });

        chk.addEventListener('change', (e) => {
          e.stopPropagation();
          updateDisplayAndFilters();
        });
      }

      optionsList.appendChild(divOpt);
    });

    if (textEl) {
      if (isSingleMonth) {
        textEl.textContent = (selectedValues.length === 1 ? selectedValues[0] : (selectedValues.length > 1 ? `${selectedValues.length} Terpilih` : 'Semua Bulan'));
      } else {
        if (selectedValues.length === 0) {
          textEl.textContent = labelMap[id];
        } else if (selectedValues.length === 1) {
          textEl.textContent = selectedValues[0];
        } else {
          textEl.textContent = `${selectedValues.length} Terpilih`;
        }
      }
    }
  }



  private refreshDashboardData(): void {
    this.fetchKPIData();
    this.fetchTrendData();
    this.fetchParetoData();
    this.fetchGridData();
  }

  private async fetchKPIData(): Promise<void> {
    try {
      const res = await fetch(`${this.apiBaseUrl}/api/analytics/kpi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.activeFilters)
      });
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        const kpi: KPIScorecard = json.data;
        this.renderScorecard(kpi);
      }
    } catch (e) {
      console.warn('KPI fetch error', e);
    }
   private formatMetricVal(val: number, type: string): string {
    if (val === undefined || val === null) return type === 'idr' ? 'Rp 0' : '0 unit';
    const isNeg = val < 0;
    const absVal = Math.abs(val);
    let str = '';
    if (type === 'idr') {
      if (absVal >= 1e9) str = `Rp ${(absVal / 1e9).toFixed(2)} Miliar`;
      else if (absVal >= 1e6) str = `Rp ${(absVal / 1e6).toFixed(2)} Juta`;
      else str = `Rp ${absVal.toLocaleString('id-ID')}`;
    } else {
      if (absVal >= 1e6) str = `${(absVal / 1e6).toFixed(2)} Juta unit`;
      else if (absVal >= 1e3) str = `${(absVal / 1e3).toFixed(1)} Ribu unit`;
      else str = `${absVal.toLocaleString('id-ID')} unit`;
    }
    return isNeg ? `-${str}` : str;
  }

  private renderScorecard(kpi: any): void {
    const elKirim = document.getElementById('valSLKirim');
    const elRealisasi = document.getElementById('valSLRealisasi');
    const elGap = document.getElementById('valSLGap');

    const badgeKirim = document.getElementById('badgeStatusKirim');
    const badgeRealisasi = document.getElementById('badgeStatusRealisasi');
    const badgeGap = document.getElementById('badgeStatusGap');

    const diffKirim = document.getElementById('diffTargetKirim');
    const diffRealisasi = document.getElementById('diffTargetRealisasi');

    const valOkKirim = document.getElementById('valOkKirim');
    const valTotalKirim = document.getElementById('valTotalKirim');
    const valOkRealisasi = document.getElementById('valOkRealisasi');
    const valTotalRealisasi = document.getElementById('valTotalRealisasi');
    const valTotalRowsCount = document.getElementById('valTotalRowsCount');
    const valGapDiffRK = document.getElementById('valGapDiffRK');
    const valGapDiffRP = document.getElementById('valGapDiffRP');

    if (elKirim) elKirim.textContent = `${kpi.sl_kirim.toFixed(1)}%`;
    if (elRealisasi) elRealisasi.textContent = `${kpi.sl_realisasi.toFixed(1)}%`;
    if (elGap) {
      elGap.textContent = `${kpi.gap >= 0 ? '+' : ''}${kpi.gap.toFixed(1)}%`;
      elGap.style.color = kpi.gap >= 0 ? '#4ADE80' : '#FF4D4D';
    }

    const progressKirim = document.getElementById('progressKirim');
    const progressRealisasi = document.getElementById('progressRealisasi');
    const progressGap = document.getElementById('progressGap');

    if (progressKirim) progressKirim.style.width = `${Math.min(100, Math.max(0, kpi.sl_kirim))}%`;
    if (progressRealisasi) progressRealisasi.style.width = `${Math.min(100, Math.max(0, kpi.sl_realisasi))}%`;
    if (progressGap) progressGap.style.width = `${Math.min(100, Math.abs(kpi.gap))}%`;

    const metricType = this.activeFilters.metric_type || 'idr';

    const diffK = kpi.sl_kirim - 85.0;
    if (badgeKirim) {
      if (kpi.sl_kirim >= 85.0) {
        badgeKirim.textContent = '✓ SESUAI TARGET';
        badgeKirim.className = 'target-badge badge-success';
      } else {
        badgeKirim.textContent = '⚠️ DI BAWAH TARGET';
        badgeKirim.className = 'target-badge badge-danger';
      }
    }
    if (diffKirim) {
      diffKirim.textContent = `${diffK >= 0 ? '+' : ''}${diffK.toFixed(1)}% vs Target`;
      diffKirim.style.color = diffK >= 0 ? '#4ADE80' : '#FF4D4D';
    }

    const diffR = kpi.sl_realisasi - 85.0;
    if (badgeRealisasi) {
      if (kpi.sl_realisasi >= 85.0) {
        badgeRealisasi.textContent = '✓ SESUAI TARGET';
        badgeRealisasi.className = 'target-badge badge-success';
      } else {
        badgeRealisasi.textContent = '⚠️ DI BAWAH TARGET';
        badgeRealisasi.className = 'target-badge badge-danger';
      }
    }
    if (diffRealisasi) {
      diffRealisasi.textContent = `${diffR >= 0 ? '+' : ''}${diffR.toFixed(1)}% vs Target`;
      diffRealisasi.style.color = diffR >= 0 ? '#4ADE80' : '#FF4D4D';
    }

    if (badgeGap) {
      badgeGap.textContent = kpi.gap >= 0 ? 'Selisih Positif' : 'Selisih Negatif';
      badgeGap.className = kpi.gap >= 0 ? 'target-badge badge-success' : 'target-badge badge-danger';
    }

    const valTotalPesanKirim = document.getElementById('valTotalPesanKirim');
    const valTotalPesanRealisasi = document.getElementById('valTotalPesanRealisasi');
    const valTotalKirimRealisasi = document.getElementById('valTotalKirimRealisasi');

    if (valTotalPesanKirim) valTotalPesanKirim.textContent = this.formatMetricVal(kpi.total_p, metricType);
    if (valTotalPesanRealisasi) valTotalPesanRealisasi.textContent = this.formatMetricVal(kpi.total_p, metricType);
    if (valTotalKirimRealisasi) valTotalKirimRealisasi.textContent = this.formatMetricVal(kpi.total_k, metricType);

    if (valOkKirim) valOkKirim.textContent = this.formatMetricVal(kpi.ok_k, metricType);
    if (valTotalKirim) valTotalKirim.textContent = this.formatMetricVal(kpi.total_k, metricType);
    if (valOkRealisasi) valOkRealisasi.textContent = this.formatMetricVal(kpi.ok_r, metricType);
    if (valTotalRealisasi) valTotalRealisasi.textContent = this.formatMetricVal(kpi.total_r, metricType);
    if (valTotalRowsCount) valTotalRowsCount.textContent = `${(kpi.cnt || 0).toLocaleString('id-ID')} Transaksi`;

    if (valGapDiffRK) {
      valGapDiffRK.textContent = this.formatMetricVal(kpi.gap_val_rk, metricType);
      valGapDiffRK.style.color = (kpi.gap_val_rk || 0) >= 0 ? '#4ADE80' : '#EF4444';
    }
    if (valGapDiffRP) {
      valGapDiffRP.textContent = this.formatMetricVal(kpi.gap_val_rp, metricType);
      valGapDiffRP.style.color = (kpi.gap_val_rp || 0) >= 0 ? '#4ADE80' : '#EF4444';
    }

  }

  private async fetchTrendData(): Promise<void> {

    try {
      const btnKirim = document.getElementById('btnTrendSLKirim');
      const activeTrendMetric = (btnKirim && btnKirim.classList.contains('active')) ? 'sl_kirim' : 'sl_realisasi';

      const res = await fetch(`${this.apiBaseUrl}/api/analytics/trend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.activeFilters)
      });
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        this.renderMonthlyTrendChart(json.data, activeTrendMetric);
      }
    } catch (e) {
      console.warn('Trend fetch error', e);
    }
  }

  private renderMonthlyTrendChart(trendList: any[], metricKey: string): void {
    const container = document.getElementById('trendChartBars');
    if (!container) return;

    if (!trendList || trendList.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); padding: 1rem;">Tidak ada data tren untuk kombinasi filter ini.</div>';
      return;
    }

    container.innerHTML = '';
    trendList.forEach(item => {
      const val = item[metricKey] || 0;
      const heightPct = Math.min(100, Math.max(10, val));
      const isAboveTarget = val >= 85.0;

      const barWrap = document.createElement('div');
      barWrap.style.flex = '1';
      barWrap.style.display = 'flex';
      barWrap.style.flexDirection = 'column';
      barWrap.style.alignItems = 'center';
      barWrap.style.justifyContent = 'flex-end';
      barWrap.style.height = '100%';

      barWrap.innerHTML = `
        <div style="font-size: 0.75rem; font-weight: 700; color: ${isAboveTarget ? '#4ADE80' : '#FF4D4D'}; margin-bottom: 0.35rem;">
          ${val.toFixed(1)}%
        </div>
        <div style="width: 60%; max-width: 45px; height: ${heightPct}%; background: ${isAboveTarget ? 'linear-gradient(180deg, #C00000 0%, #8B0000 100%)' : '#FF4D4D'}; border-radius: 4px 4px 0 0; transition: height 0.3s ease;"></div>
        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">${item.month}</div>
      `;
      container.appendChild(barWrap);
    });
  }

  private async fetchParetoData(): Promise<void> {
    try {
      const payload = {
        ...this.activeFilters,
        dimension: this.activeParetoDimension
      };
      const res = await fetch(`${this.apiBaseUrl}/api/analytics/pareto`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        this.renderParetoTreeMaps(json.data);
      }
    } catch (e) {
      console.warn('Pareto fetch error', e);
    }
  }

  private renderParetoTreeMaps(items: ParetoItem[]): void {
    const grid = document.getElementById('treemapGrid');
    if (!grid) return;

    if (!items || items.length === 0) {
      grid.innerHTML = '<div style="color: var(--text-muted); padding: 1rem;">Tidak ada data Pareto untuk kombinasi filter ini.</div>';
      return;
    }

    grid.innerHTML = '';
    items.slice(0, 12).forEach(it => {
      const box = document.createElement('div');
      box.className = 'treemap-box';
      box.innerHTML = `
        <div class="treemap-title">${it.name}</div>
        <div class="treemap-val">${this.activeFilters.metric_type === 'idr' ? 'Rp ' + it.value.toLocaleString('id-ID') : it.value.toLocaleString('id-ID') + ' unit'}</div>
        <div class="treemap-pct">Kontribusi: ${it.percentage.toFixed(1)}% (Kumulatif: ${it.cumulative_percentage.toFixed(1)}%)</div>
      `;

      box.addEventListener('click', () => {
        if (this.activeParetoDimension === 'alasan') {
          this.activeFilters.reason = it.name;
        } else if (this.activeParetoDimension === 'cabang') {
          this.activeFilters.branches = [it.name];
        } else if (this.activeParetoDimension === 'mtm_alias') {
          this.activeFilters.mtm_aliases = [it.name];
        } else if (this.activeParetoDimension === 'grup_brand') {
          this.activeFilters.brand_groups = [it.name];
        } else if (this.activeParetoDimension === 'item') {
          this.activeFilters.items = [it.name];
        }
        this.refreshDashboardData();
      });

      grid.appendChild(box);
    });
  }

  private async fetchGridData(): Promise<void> {
    try {
      const res = await fetch(`${this.apiBaseUrl}/api/analytics/grid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...this.activeFilters, limit: 50 })
      });
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        this.renderDetailGrid(json.data);
      }
    } catch (e) {
      console.warn('Grid fetch error', e);
    }
  }

  renderDetailGrid(records: GridRecord[]): void {
    const tbody = document.getElementById('gridTbody');
    const badge = document.getElementById('gridCountBadge');

    if (badge) badge.textContent = `${records.length} Transaksi Terfilter`;
    if (!tbody) return;

    if (!records || records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">Tidak ada transaksi yang cocok.</td></tr>';
      return;
    }

    tbody.innerHTML = records.map(r => `
      <tr>
        <td>${r.month}</td>
        <td>${r.mtm_type}</td>
        <td>${r.branch}</td>
        <td>${r.mtm_alias}</td>
        <td>${r.brand_group}</td>
        <td>${r.item_name}</td>
        <td>Rp ${(r.idr_kirim || 0).toLocaleString('id-ID')}</td>
        <td>Rp ${(r.idr_realisasi || 0).toLocaleString('id-ID')}</td>
        <td><span style="color: ${r.reason_final.includes('On-Time') ? '#4ADE80' : '#FFD700'};">${r.reason_final}</span></td>
      </tr>
    `).join('');
  }
}

window.addEventListener('DOMContentLoaded', () => {
  new DashboardApp();
});
