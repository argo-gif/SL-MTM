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
  private isParetoUnfulfill: boolean = true;

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

    // Pareto Switcher Mode (Unfulfill vs All)
    // Pareto Mode strictly defaults to Unfulfill Problem Analysis
    this.isParetoUnfulfill = true;


    // Pareto Tabs
    const tabs = document.querySelectorAll('.pareto-tab');
    tabs.forEach(t => {
      t.addEventListener('click', (e) => {
        tabs.forEach(x => x.classList.remove('active'));
        const target = e.target as HTMLElement;
        target.classList.add('active');
        this.activeParetoDimension = target.getAttribute('data-dim') || 'alasan';
        this.fetchParetoData();
        this.fetchGridData();
      });
    });

    // Global listener to deselect treemap cross-filter when clicking outside treemap tiles
    document.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      if (!target) return;

      const insideTreemapSection = target.closest('.pareto-container') || target.closest('#treemapGrid');
      const insideTile = target.closest('.tableau-tile');
      const insideSelect = target.closest('.custom-select-container');
      const insideModal = target.closest('.modal-overlay');

      if (insideTreemapSection && !insideTile && !insideSelect && !insideModal) {
        this.clearParetoCrossFilter();
      }
    });



    // PPT Direct Export (Cetak Semua PPT Langsung Tanpa Modal)
    const btnOpenExport = document.getElementById('btnOpenExportModal') as HTMLButtonElement;

    btnOpenExport?.addEventListener('click', async () => {
      if (btnOpenExport.disabled) return;

      const originalText = btnOpenExport.textContent;
      btnOpenExport.disabled = true;
      btnOpenExport.textContent = '⏳ Mencetak PPT...';

      try {
        const payload = {
          ...this.activeFilters,
          selected_modules: {
            kpi_summary: true,
            pareto_sheets: true,
            detail_grid: true
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
      } catch (err: any) {
        alert(err.message || 'Gagal ekspor PPT.');
      } finally {
        btnOpenExport.disabled = false;
        btnOpenExport.textContent = originalText;
      }
    });

    // Upload Dataset Modal
    const uploadModal = document.getElementById('uploadModal');
    const btnOpenUpload = document.getElementById('btnOpenUploadModal');
    const btnCloseUpload = document.getElementById('btnCloseUploadModal');
    const uploadForm = document.getElementById('uploadForm');

    btnOpenUpload?.addEventListener('click', (e) => {
      e.stopPropagation();
      if (uploadModal) uploadModal.style.display = 'flex';
      const monthInput = document.getElementById('uploadDeliveryMonth') as HTMLInputElement;
      if (monthInput) {
        let activeM = this.activeFilters.month;
        if (!activeM || !/^\d{4}-\d{2}$/.test(activeM)) {
          activeM = '2026-08';
        }
        monthInput.value = activeM;
      }
      const passInput = document.getElementById('uploadPasswordInput') as HTMLInputElement;
      if (passInput) passInput.value = '';

      const progressWrapper = document.getElementById('uploadProgressWrapper');
      if (progressWrapper) progressWrapper.style.display = 'none';
      const progressBar = document.getElementById('uploadProgressBar');
      if (progressBar) {
        progressBar.style.width = '0%';
        progressBar.style.background = 'linear-gradient(90deg, #D97706 0%, #FBBF24 50%, #10B981 100%)';
      }

      const statusMsg = document.getElementById('uploadStatusMsg');
      if (statusMsg) statusMsg.style.display = 'none';
    });

    btnCloseUpload?.addEventListener('click', () => {
      if (uploadModal) uploadModal.style.display = 'none';
    });

    uploadModal?.addEventListener('click', (e) => {
      if (e.target === uploadModal) {
        uploadModal.style.display = 'none';
      }
    });

    uploadForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const monthInput = document.getElementById('uploadDeliveryMonth') as HTMLInputElement;
      const fileInput = document.getElementById('datasetFileInput') as HTMLInputElement;
      const passInput = document.getElementById('uploadPasswordInput') as HTMLInputElement;
      const statusMsg = document.getElementById('uploadStatusMsg');
      const btnConfirm = document.getElementById('btnConfirmUpload') as HTMLButtonElement;

      const progressWrapper = document.getElementById('uploadProgressWrapper');
      const progressStage = document.getElementById('uploadProgressStage');
      const progressPercent = document.getElementById('uploadProgressPercent');
      const progressBar = document.getElementById('uploadProgressBar');

      const updateProgress = (percent: number, stageText: string, isError = false, isSuccess = false) => {
        if (progressWrapper) progressWrapper.style.display = 'block';
        if (progressPercent) progressPercent.textContent = `${percent}%`;
        if (progressBar) {
          progressBar.style.width = `${percent}%`;
          if (isError) {
            progressBar.style.background = '#EF4444';
            progressBar.style.boxShadow = '0 0 10px rgba(239, 68, 68, 0.6)';
          } else if (isSuccess) {
            progressBar.style.background = '#10B981';
            progressBar.style.boxShadow = '0 0 10px rgba(16, 185, 129, 0.6)';
          } else {
            progressBar.style.background = 'linear-gradient(90deg, #D97706 0%, #FBBF24 50%, #10B981 100%)';
            progressBar.style.boxShadow = '0 0 10px rgba(251, 191, 36, 0.6)';
          }
        }
        if (progressStage && stageText) {
          progressStage.textContent = stageText;
          if (isError) progressStage.style.color = '#FCA5A5';
          else if (isSuccess) progressStage.style.color = '#34D399';
          else progressStage.style.color = '#FDE047';
        }
      };

      const periodeInput = document.getElementById('uploadPeriodeInput') as HTMLInputElement;
      const targetMonth = periodeInput ? periodeInput.value.trim() : '2026-08';
      const targetYear = targetMonth.split('-')[0] || '2026';
      const targetMonthVal = targetMonth.split('-')[1] || '08';
      const uploadPassword = passInput ? passInput.value.trim() : '';

      if (!targetMonth) {
        updateProgress(0, '❌ Harap pilih Periode Data terlebih dahulu.', true);
        return;
      }

      if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        updateProgress(0, '❌ Silakan pilih file Excel (.xlsx) terlebih dahulu.', true);
        return;
      }

      if (!uploadPassword) {
        updateProgress(0, '❌ Harap masukkan Password Akses Upload terlebih dahulu.', true);
        return;
      }

      if (uploadPassword !== 'Adelle@0403') {
        updateProgress(0, '❌ Password Akses Upload salah! Masukkan Adelle@0403.', true);
        return;
      }

      const file = fileInput.files[0];
      if (btnConfirm) {
        btnConfirm.disabled = true;
        btnConfirm.textContent = 'Memproses Upload Data...';
      }
      if (statusMsg) statusMsg.style.display = 'none';

      updateProgress(5, `⏳ 1/3 Mengunggah file Excel (5%)...`);

      let simulatedInterval: any = null;
      try {
        const formData = new FormData();
        formData.append('target_year', targetYear);
        formData.append('target_month_num', targetMonthVal);
        formData.append('target_month', targetMonth);
        formData.append('password', uploadPassword);
        formData.append('file', file);

        const url = `${this.apiBaseUrl}/api/data/upload?target_month=${encodeURIComponent(targetMonth)}&target_year=${encodeURIComponent(targetYear)}&target_month_num=${encodeURIComponent(targetMonthVal)}`;
        
        const uploadResult: any = await new Promise((resolve, reject) => {
          const xhr = new XMLHttpRequest();
          xhr.open('POST', url, true);
          xhr.setRequestHeader('X-Target-Year', targetYear);
          xhr.setRequestHeader('X-Target-Month', targetMonth);
          xhr.setRequestHeader('X-Upload-Password', uploadPassword);

          const startSimulatedProcessing = () => {
            if (simulatedInterval) return;
            let currentPct = 71;
            updateProgress(71, `⏳ 2/3 Membaca & memverifikasi baris Excel periode ${targetMonth}...`);
            simulatedInterval = setInterval(() => {
              if (currentPct < 98) {
                currentPct += 1;
                if (currentPct >= 86) {
                  updateProgress(currentPct, `⏳ 3/3 Memperbarui database & indeks transaksi periode ${targetMonth}...`);
                } else {
                  updateProgress(currentPct, `⏳ 2/3 Membaca & memverifikasi baris Excel periode ${targetMonth}...`);
                }
              }
            }, 120);
          };

          xhr.upload.addEventListener('progress', (ev) => {
            if (ev.lengthComputable) {
              const rawRatio = ev.loaded / ev.total;
              const uploadPct = Math.min(70, Math.max(5, Math.round(rawRatio * 70)));
              updateProgress(uploadPct, `⏳ 1/3 Mengunggah file Excel (${uploadPct}%)...`);

              if (rawRatio >= 0.98 || uploadPct >= 69) {
                startSimulatedProcessing();
              }
            }
          });

          xhr.upload.addEventListener('load', () => {
            startSimulatedProcessing();
          });

          xhr.onload = () => {
            if (simulatedInterval) clearInterval(simulatedInterval);
            try {
              const json = JSON.parse(xhr.responseText);
              resolve({ ok: xhr.status >= 200 && xhr.status < 300, status: xhr.status, json });
            } catch (err) {
              reject(new Error('Format respon server tidak valid.'));
            }
          };

          xhr.onerror = () => {
            if (simulatedInterval) clearInterval(simulatedInterval);
            reject(new Error('Koneksi server terputus.'));
          };

          xhr.send(formData);
        });

        const json = uploadResult.json;
        if (uploadResult.ok && json.status === 'success') {
          updateProgress(100, `✅ 100% Selesai! ${json.message}`, false, true);
          if (statusMsg) {
            statusMsg.style.display = 'block';
            statusMsg.style.background = 'rgba(16, 185, 129, 0.18)';
            statusMsg.style.border = '1px solid #10B981';
            statusMsg.style.color = '#34D399';
            statusMsg.innerHTML = `✅ <strong>Berhasil!</strong> ${json.message}`;
          }
          setTimeout(() => {
            if (uploadModal) uploadModal.style.display = 'none';
            this.activeFilters.month = targetMonth;
            this.loadFilterOptions();
            this.refreshDashboardData();
          }, 1800);
        } else {
          updateProgress(100, `❌ Gagal: ${json?.message || 'Verifikasi data gagal.'}`, true, false);
          if (statusMsg) {
            statusMsg.style.display = 'block';
            statusMsg.style.background = 'rgba(239, 68, 68, 0.18)';
            statusMsg.style.border = '1px solid #EF4444';
            statusMsg.style.color = '#FCA5A5';
            statusMsg.innerHTML = `❌ <strong>Gagal:</strong> ${json?.message || 'Terjadi kesalahan saat mengunggah.'}`;
          }
        }
      } catch (err: any) {
        if (simulatedInterval) clearInterval(simulatedInterval);
        updateProgress(100, `❌ Gagal: ${err.message}`, true, false);
        if (statusMsg) {
          statusMsg.style.display = 'block';
          statusMsg.style.background = 'rgba(239, 68, 68, 0.18)';
          statusMsg.style.border = '1px solid #EF4444';
          statusMsg.style.color = '#FCA5A5';
          statusMsg.innerHTML = `❌ <strong>Error:</strong> ${err.message}`;
        }
      } finally {
        if (btnConfirm) {
          btnConfirm.disabled = false;
          btnConfirm.textContent = '⚡ Verifikasi & Update Data Periode';
        }
      }
    });
  }

  private updateUserUI(): void {
    const user = this.authController.getCurrentUser();
    const badge = document.getElementById('userRoleBadge');
    const btn = document.getElementById('btnLoginLogout');
    const btnUpload = document.getElementById('btnOpenUploadModal');

    if (btnUpload) {
      btnUpload.style.display = 'inline-flex';
    }

    if (user) {
      if (badge) {
        badge.textContent = `${user.role.toUpperCase()}: ${user.username}`;
        badge.className = `role-badge ${user.role}`;
      }
      if (btn) btn.textContent = 'Logout';
    } else {
      if (badge) {
        badge.textContent = 'ADMIN';
        badge.className = 'role-badge admin';
      }
      if (btn) btn.textContent = 'Login';
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

  private formatMonthLabel(monthStr: string): string {
    if (!monthStr || monthStr === 'Semua Bulan' || monthStr === 'ALL') return monthStr;
    const parts = String(monthStr).trim().split('-');
    if (parts.length === 2) {
      const yr = parts[0];
      const mo = parts[1];
      const monthMap: Record<string, string> = {
        '01': 'JAN', '02': 'FEB', '03': 'MAR', '04': 'APR',
        '05': 'MEI', '06': 'JUN', '07': 'JUL', '08': 'AGU',
        '09': 'SEP', '10': 'OKT', '11': 'NOV', '12': 'DES'
      };
      if (monthMap[mo]) {
        return `${monthMap[mo]}-${yr}`;
      }
    }
    return monthStr;
  }

  private renderMonthlyTrendChart(trendList: any[], metricKey: string): void {
    const container = document.getElementById('trendChartBars');
    if (!container) return;

    if (!trendList || trendList.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); padding: 1rem;">Tidak ada data tren untuk kombinasi filter ini.</div>';
      return;
    }

    const metricType = this.activeFilters.metric_type || 'idr';
    container.innerHTML = '';

    trendList.forEach(item => {
      const val = item[metricKey] || 0;
      const heightPct = Math.min(100, Math.max(12, val));
      const isAboveTarget = val >= 85.0;

      const barWrap = document.createElement('div');
      barWrap.style.flex = '1';
      barWrap.style.minWidth = '132px';
      barWrap.style.display = 'flex';
      barWrap.style.flexDirection = 'column';
      barWrap.style.alignItems = 'center';
      barWrap.style.justifyContent = 'flex-end';
      barWrap.style.height = '100%';

      const barBg = isAboveTarget
        ? 'linear-gradient(180deg, #10B981 0%, #047857 100%)'
        : 'linear-gradient(180deg, #EF4444 0%, #991B1B 100%)';
      const textColor = isAboveTarget ? '#4ADE80' : '#FCA5A5';

      const strP = this.formatMetricVal(item.total_p, metricType);
      const strK = this.formatMetricVal(item.total_k, metricType);
      const strR = this.formatMetricVal(item.total_r, metricType);

      const isSLKirim = (metricKey === 'sl_kirim');

      barWrap.innerHTML = `
        <div style="font-size: 0.78rem; font-weight: 700; color: ${textColor}; margin-bottom: 0.25rem;">
          ${val.toFixed(1)}%
        </div>
        <div style="width: 50%; max-width: 44px; height: ${heightPct * 1.1}px; background: ${barBg}; border-radius: 6px 6px 0 0; transition: height 0.3s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.4);"></div>
        <div style="font-size: 0.78rem; font-weight: 700; color: white; margin-top: 0.35rem; margin-bottom: 0.25rem;">${this.formatMonthLabel(item.month)}</div>
        
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; padding: 0.35rem 0.45rem; width: 100%; font-size: 0.67rem; display: flex; flex-direction: column; gap: 3px; box-shadow: 0 2px 8px rgba(0,0,0,0.5);">
          <div style="display:flex; justify-content:space-between; align-items:center; color:#94A3B8; white-space:nowrap;">
            <span>📋 Pesan:</span>
            <strong style="color:white; font-weight:700; margin-left:4px;">${strP}</strong>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; color:#94A3B8; white-space:nowrap;">
            <span>${isSLKirim ? '🚚 Kirim:' : '✅ Realisasi:'}</span>
            <strong style="color:white; font-weight:700; margin-left:4px;">${isSLKirim ? strK : strR}</strong>
          </div>
        </div>
      `;
      container.appendChild(barWrap);
    });
  }





  private async fetchParetoData(): Promise<void> {
    try {
      const payload = {
        ...this.activeFilters,
        dimension: this.activeParetoDimension,
        unfulfill_only: (this.isParetoUnfulfill !== undefined ? this.isParetoUnfulfill : true)
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
    const container = document.getElementById('treemapGrid');
    if (!container) return;

    // Filter out zero-value items so they don't clog the treemap canvas
    const nonZeroItems = (items || []).filter(it => it.value > 0);

    if (!nonZeroItems || nonZeroItems.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); padding: 1.5rem;">Tidak ada data Tree Maps untuk kombinasi filter ini.</div>';
      return;
    }

    container.innerHTML = '';
    const metricType = this.activeFilters.metric_type || 'idr';

    // Find cutoff index where cumulative_percentage >= 80% (min 80% rule)
    let vitalIndexCutoff = 0;
    for (let i = 0; i < nonZeroItems.length; i++) {
      vitalIndexCutoff = i;
      if (nonZeroItems[i].cumulative_percentage >= 80.0) {
        break;
      }
    }

    const displayCount = Math.max(vitalIndexCutoff + 1, Math.min(nonZeroItems.length, 12));
    const displayItems = nonZeroItems.slice(0, displayCount);

    const execWrap = document.createElement('div');
    execWrap.className = 'tableau-executive-treemap';

    // Tableau Style Legend Bar
    const legendBar = document.createElement('div');
    legendBar.className = 'tableau-legend-bar';
    legendBar.innerHTML = `
      <div style="font-size: 0.75rem; font-weight: 700; color: #FFFFFF; display:flex; align-items:center; gap:0.4rem;">
        <span style="color: var(--konimex-gold);">📊</span> LEGENDA INTENSITAS PARETO:
      </div>
      <div class="tableau-legend-items">
        <div><span class="tableau-legend-dot" style="background: #DC2626; box-shadow: 0 0 6px #F87171;"></span> ⭐ Top #1 (Dominan)</div>
        <div><span class="tableau-legend-dot" style="background: #EA580C; box-shadow: 0 0 6px #FB923C;"></span> 🔥 Top #2-#3 (Dampak Tinggi)</div>
        <div><span class="tableau-legend-dot" style="background: #D97706; box-shadow: 0 0 6px #FBBF24;"></span> 🟨 Vital 80% (Dampak Menengah)</div>
        <div><span class="tableau-legend-dot" style="background: #1D4ED8; box-shadow: 0 0 6px #60A5FA;"></span> 🟦 Minor (< 20%)</div>
      </div>
    `;


    execWrap.appendChild(legendBar);

    const flexGrid = document.createElement('div');
    flexGrid.className = 'tableau-treemap-flex-grid';

    displayItems.forEach((it, idx) => {
      const tile = document.createElement('div');
      const isVital = idx <= vitalIndexCutoff;

      // Tableau Heatmap Gradient Class
      let colorClass = 'tableau-color-slate';
      if (idx === 0) colorClass = 'tableau-color-top';
      else if (idx === 1 || idx === 2) colorClass = 'tableau-color-high';
      else if (isVital) colorClass = 'tableau-color-medium';

      tile.className = `tableau-tile ${colorClass}`;

      // Dynamic proportional flex sizing so every single vital tile fits neatly
      let flexBasis = '130px';
      let minHeight = '85px';
      let titleSize = '0.78rem';
      let valSize = '0.92rem';

      if (it.percentage >= 25.0) {
        flexBasis = '320px';
        minHeight = '145px';
        titleSize = '1.05rem';
        valSize = '1.4rem';
      } else if (it.percentage >= 12.0) {
        flexBasis = '250px';
        minHeight = '125px';
        titleSize = '0.95rem';
        valSize = '1.2rem';
      } else if (it.percentage >= 6.0) {
        flexBasis = '190px';
        minHeight = '105px';
        titleSize = '0.88rem';
        valSize = '1.05rem';
      } else if (it.percentage >= 3.0) {
        flexBasis = '145px';
        minHeight = '90px';
        titleSize = '0.8rem';
        valSize = '0.92rem';
      }

      tile.style.flex = `1 1 ${flexBasis}`;
      tile.style.minHeight = minHeight;

      const isSelected = (
        (this.activeParetoDimension === 'alasan' && this.activeFilters.reason === it.name) ||
        (this.activeParetoDimension === 'cabang' && this.activeFilters.branches.includes(it.name)) ||
        (this.activeParetoDimension === 'mtm_alias' && this.activeFilters.mtm_aliases.includes(it.name)) ||
        (this.activeParetoDimension === 'grup_brand' && this.activeFilters.brand_groups.includes(it.name)) ||
        (this.activeParetoDimension === 'item' && this.activeFilters.items.includes(it.name))
      );
      if (isSelected) tile.classList.add('selected');

      const valStr = this.formatMetricVal(it.value, metricType);
      const badgeHtml = isVital
        ? `<span style="font-size: 0.62rem; font-weight: 700; color: #FDE047; background: rgba(0,0,0,0.4); border: 1px solid rgba(234,179,8,0.5); padding: 0.12rem 0.4rem; border-radius: 4px; float: right;">⭐ Vital 80%</span>`
        : ``;

      tile.innerHTML = `
        <div>
          ${badgeHtml}
          <div class="treemap-title" style="font-size: ${titleSize}; text-transform: uppercase; line-height: 1.2;">${it.name}</div>
        </div>
        <div style="margin-top: 0.35rem;">
          <div class="treemap-val" style="font-size: ${valSize}; text-shadow: 0 2px 8px rgba(0,0,0,0.5);">${valStr}</div>
          <div style="font-size: 0.68rem; color: rgba(255,255,255,0.85); margin-top: 0.2rem;">
            Kontribusi: <strong style="color: #FDE047;">${it.percentage.toFixed(1)}%</strong> <span style="opacity:0.8;">(Kumulatif: ${it.cumulative_percentage.toFixed(1)}%)</span>
          </div>
        </div>
      `;

      tile.addEventListener('click', (e) => {
        e.stopPropagation();
        this.handleTreemapClick(it.name);
      });

      flexGrid.appendChild(tile);
    });

    execWrap.appendChild(flexGrid);
    container.appendChild(execWrap);

    this.updateCrossFilterBadge();
  }

  private clearParetoCrossFilter(): void {
    let changed = false;
    if (this.activeFilters.reason) {
      delete this.activeFilters.reason;
      changed = true;
    }
    if (this.activeFilters.branches && this.activeFilters.branches.length > 0) {
      this.activeFilters.branches = [];
      changed = true;
    }
    if (this.activeFilters.mtm_aliases && this.activeFilters.mtm_aliases.length > 0) {
      this.activeFilters.mtm_aliases = [];
      changed = true;
    }
    if (this.activeFilters.brand_groups && this.activeFilters.brand_groups.length > 0) {
      this.activeFilters.brand_groups = [];
      changed = true;
    }
    if (this.activeFilters.items && this.activeFilters.items.length > 0) {
      this.activeFilters.items = [];
      changed = true;
    }

    if (changed) {
      this.updateCrossFilterBadge();
      this.refreshDashboardData();
    }
  }

  private updateCrossFilterBadge(): void {
    const badge = document.getElementById('crossFilterBadge');
    if (!badge) return;

    let activeFilterName = '';
    if (this.activeParetoDimension === 'alasan' && this.activeFilters.reason) {
      activeFilterName = this.activeFilters.reason;
    } else if (this.activeParetoDimension === 'cabang' && this.activeFilters.branches && this.activeFilters.branches.length > 0) {
      activeFilterName = this.activeFilters.branches[0];
    } else if (this.activeParetoDimension === 'mtm_alias' && this.activeFilters.mtm_aliases && this.activeFilters.mtm_aliases.length > 0) {
      activeFilterName = this.activeFilters.mtm_aliases[0];
    } else if (this.activeParetoDimension === 'grup_brand' && this.activeFilters.brand_groups && this.activeFilters.brand_groups.length > 0) {
      activeFilterName = this.activeFilters.brand_groups[0];
    } else if (this.activeParetoDimension === 'item' && this.activeFilters.items && this.activeFilters.items.length > 0) {
      activeFilterName = this.activeFilters.items[0];
    }

    if (activeFilterName) {
      badge.style.background = 'rgba(234, 179, 8, 0.2)';
      badge.style.borderColor = '#EAB308';
      badge.style.color = '#FDE047';
      badge.innerHTML = `🔍 Filter Aktif: <strong>${activeFilterName}</strong> <span style="margin-left: 4px; background: rgba(0,0,0,0.3); padding: 1px 6px; border-radius: 8px;">(Klik luar / di sini untuk melepas ✕)</span>`;
      badge.style.cursor = 'pointer';
      badge.onclick = (e) => {
        e.stopPropagation();
        this.clearParetoCrossFilter();
      };
    } else {
      badge.style.background = 'rgba(255, 255, 255, 0.05)';
      badge.style.borderColor = 'rgba(255, 255, 255, 0.1)';
      badge.style.color = 'var(--text-muted)';
      badge.innerHTML = 'Klik kotak Treemap untuk Cross-Filter';
      badge.style.cursor = 'default';
      badge.onclick = null;
    }
  }

  private handleTreemapClick(itemName: string): void {
    if (this.activeParetoDimension === 'alasan') {
      this.activeFilters.reason = (this.activeFilters.reason === itemName) ? '' : itemName;
    } else if (this.activeParetoDimension === 'cabang') {
      this.activeFilters.branches = this.activeFilters.branches.includes(itemName) ? [] : [itemName];
    } else if (this.activeParetoDimension === 'mtm_alias') {
      this.activeFilters.mtm_aliases = this.activeFilters.mtm_aliases.includes(itemName) ? [] : [itemName];
    } else if (this.activeParetoDimension === 'grup_brand') {
      this.activeFilters.brand_groups = this.activeFilters.brand_groups.includes(itemName) ? [] : [itemName];
    } else if (this.activeParetoDimension === 'item') {
      this.activeFilters.items = this.activeFilters.items.includes(itemName) ? [] : [itemName];
    }
    this.updateCrossFilterBadge();
    this.refreshDashboardData();
  }



  private async fetchGridData(): Promise<void> {
    try {
      const payload = {
        ...this.activeFilters,
        dimension: this.activeParetoDimension,
        limit: 50
      };
      const res = await fetch(`${this.apiBaseUrl}/api/analytics/grid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        this.renderDetailGrid(json.data);
      }
    } catch (e) {
      console.warn('Grid fetch error', e);
    }
  }

  private renderDetailGrid(records: any[]): void {
    const tbody = document.getElementById('gridTbody');
    const badge = document.getElementById('gridCountBadge');
    const titleEl = document.getElementById('gridTableTitle');
    const thDimEl = document.getElementById('thDimName');

    const dimLabelMap: Record<string, string> = {
      'alasan': 'Alasan Keterlambatan / Unfulfill',
      'mtm_alias': 'Akun MTM Alias',
      'cabang': 'Nama Cabang',
      'grup_brand': 'Grup Brand',
      'item': 'Item / Nama Item'
    };

    const currentDim = this.activeParetoDimension || 'alasan';
    const dimLabel = dimLabelMap[currentDim] || 'Dimensi Analisis';
    const metricType = this.activeFilters.metric_type || 'idr';

    if (titleEl) titleEl.textContent = `Tabel Detail Analisis Berdasarkan ${dimLabel}`;
    if (thDimEl) thDimEl.textContent = dimLabel;
    if (badge) badge.textContent = `${records ? records.length : 0} Data Terfilter`;
    if (!tbody) return;

    if (!records || records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Tidak ada data analisis yang cocok.</td></tr>';
      return;
    }

    tbody.innerHTML = records.map((r, idx) => {
      const valP = this.formatMetricVal(r.total_pesan, metricType);
      const valK = this.formatMetricVal(r.total_kirim, metricType);
      const valR = this.formatMetricVal(r.total_realisasi, metricType);
      const valGap = this.formatMetricVal(r.gap_unfulfill, metricType);

      const isVital = r.is_vital;
      const statusBadge = isVital
        ? `<span style="font-size: 0.7rem; font-weight: 700; color: #FDE047; background: rgba(220,38,38,0.25); border: 1px solid #F87171; padding: 0.15rem 0.45rem; border-radius: 4px;">⭐ Vital 80%</span>`
        : `<span style="font-size: 0.7rem; font-weight: 600; color: #94A3B8; background: rgba(255,255,255,0.05); padding: 0.15rem 0.45rem; border-radius: 4px;">Minor</span>`;

      return `
        <tr>
          <td style="text-align: center; font-weight: 600; color: var(--text-muted);">${idx + 1}</td>
          <td style="font-weight: 700; color: #FFFFFF;">${r.name}</td>
          <td style="text-align: right; color: #CBD5E1;">${valP}</td>
          <td style="text-align: right; color: #4ADE80;">${valK}</td>
          <td style="text-align: right; color: #FBBF24;">${valR}</td>
          <td style="text-align: right; font-weight: 800; color: #EF4444;">${valGap}</td>
          <td style="text-align: center; font-weight: 700; color: ${r.sl_kirim >= 85 ? '#4ADE80' : '#EF4444'};">${r.sl_kirim.toFixed(1)}%</td>
          <td style="text-align: center; font-weight: 700; color: ${r.sl_realisasi >= 85 ? '#4ADE80' : '#EF4444'};">${r.sl_realisasi.toFixed(1)}%</td>
          <td style="text-align: center;">${statusBadge}</td>
        </tr>
      `;
    }).join('');
  }


}

window.addEventListener('DOMContentLoaded', () => {
  new DashboardApp();
});
