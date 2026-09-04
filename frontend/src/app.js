import { AuthController } from './auth.js';

class DashboardApp {
  constructor() {
    this.authController = new AuthController();
    this.apiBaseUrl = (typeof window !== 'undefined' && window.location.origin && !window.location.origin.startsWith('file')) ? '' : 'http://127.0.0.1:5000';

    this.activeFilters = {
      months: [],
      month: '',
      mtm_types: ['KA'],
      mtm_type: 'KA',
      branches: [],
      mtm_aliases: [],
      brand_groups: [],
      items: [],
      metric_type: 'idr',
      sl_type: 'sl_kirim'
    };
    this.activeParetoDimension = 'alasan';
    this.isParetoUnfulfill = true;
    this.treemapCrossFilter = null;

    this.initDOM();

    this.setupCustomSelectListeners();
    this.setupEventListeners();
    this.checkAuthenticationGate();
  }

  initDOM() {
    console.log('Initializing MTM Dashboard App...');
  }

  checkAuthenticationGate() {
    const gateView = document.getElementById('loginGateView');
    const appContent = document.getElementById('appDashboardContent');

    if (gateView) gateView.style.display = 'none';
    if (appContent) appContent.style.display = 'block';

    const btnUpload = document.getElementById('btnOpenUploadModal');
    if (btnUpload) btnUpload.style.display = 'inline-flex';

    this.updateUserUI();
    this.loadFilterOptions();
  }



  setupCustomSelectListeners() {
    document.querySelectorAll('.custom-select-container').forEach(container => {
      const trigger = container.querySelector('.custom-select-trigger');
      const searchInput = container.querySelector('.custom-search-input');

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
              Array.from(optionsList.querySelectorAll('.custom-option')).forEach(opt => opt.style.display = '');
            }
            setTimeout(() => searchInput.focus(), 50);
          }
        }
      });

      searchInput?.addEventListener('input', (e) => {
        const kw = (e.target.value || '').toLowerCase().trim();
        const optionsList = container.querySelector('.custom-options-list');
        if (!optionsList) return;
        Array.from(optionsList.querySelectorAll('.custom-option')).forEach(opt => {
          const txt = opt.textContent.toLowerCase();
          opt.style.display = txt.includes(kw) ? '' : 'none';
        });
      });
    });

    document.addEventListener('click', () => {
      document.querySelectorAll('.custom-select-container.open').forEach(c => c.classList.remove('open'));
    });
  }

  setupEventListeners() {
    // Mandatory Gate Login Form
    const loginFormGate = document.getElementById('loginFormGate');
    const btnLoginGate = document.querySelector('.login-gate-btn');

    const handleGateLogin = async (e) => {
      if (e) e.preventDefault();
      const userVal = document.getElementById('usernameInputGate')?.value || '';
      const passVal = document.getElementById('passwordInputGate')?.value || '';
      const errBox = document.getElementById('loginGateError');

      try {
        if (errBox) errBox.style.display = 'none';
        await this.authController.login(userVal, passVal, this.apiBaseUrl);
        this.checkAuthenticationGate();
      } catch (err) {
        if (errBox) {
          errBox.textContent = err.message || 'Login gagal. Periksa username dan password.';
          errBox.style.display = 'block';
        }
      }
    };

    loginFormGate?.addEventListener('submit', handleGateLogin);
    btnLoginGate?.addEventListener('click', handleGateLogin);


    // Logout Trigger
    const btnLoginLogout = document.getElementById('btnLoginLogout');
    btnLoginLogout?.addEventListener('click', () => {
      this.authController.clearSession();
      this.checkAuthenticationGate();
    });

    // SL Mode Toggle (SL Kirim vs SL Realisasi)
    const btnTrendKirim = document.getElementById('btnTrendSLKirim');
    const btnTrendRealisasi = document.getElementById('btnTrendSLRealisasi');
    const btnParetoKirim = document.getElementById('btnParetoSLKirim');
    const btnParetoRealisasi = document.getElementById('btnParetoSLRealisasi');

    const updateSLMode = (slType) => {
      this.activeFilters.sl_type = slType;
      const isKirim = (slType === 'sl_kirim');

      if (btnTrendKirim && btnTrendRealisasi) {
        btnTrendKirim.classList.toggle('active', isKirim);
        btnTrendRealisasi.classList.toggle('active', !isKirim);
      }
      if (btnParetoKirim && btnParetoRealisasi) {
        btnParetoKirim.classList.toggle('active', isKirim);
        btnParetoRealisasi.classList.toggle('active', !isKirim);
      }

      const badgePareto = document.getElementById('badgeParetoSLMode');
      if (badgePareto) {
        badgePareto.textContent = isKirim ? '⚠️ GAP: SL Kirim (Pesan - Kirim)' : '⚠️ GAP: SL Realisasi (Pesan - Realisasi)';
      }

      const thGapHeader = document.getElementById('thGapHeader');
      if (thGapHeader) {
        thGapHeader.textContent = isKirim ? 'Gap Unfulfilled (Pesan - Kirim)' : 'Gap Unfulfilled (Pesan - Realisasi)';
      }

      this.refreshDashboardData();
    };

    btnTrendKirim?.addEventListener('click', () => updateSLMode('sl_kirim'));
    btnTrendRealisasi?.addEventListener('click', () => updateSLMode('sl_realisasi'));
    btnParetoKirim?.addEventListener('click', () => updateSLMode('sl_kirim'));
    btnParetoRealisasi?.addEventListener('click', () => updateSLMode('sl_realisasi'));

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
      const defaultM = this.latestMonthDefault || '2026-08';
      const defaultT = this.defaultMTMTypeDefault || 'KA';

      this.activeFilters = {
        months: [defaultM],
        month: defaultM,
        mtm_types: [defaultT],
        mtm_type: defaultT,
        branches: [],
        mtm_aliases: [],
        brand_groups: [],
        items: [],
        reasons: [],
        metric_type: this.activeFilters.metric_type || 'idr',
        sl_type: 'sl_kirim'
      };
      this.treemapCrossFilter = null;

      document.querySelectorAll('.custom-option-checkbox').forEach(cb => cb.checked = false);
      document.querySelectorAll('.custom-option').forEach(opt => opt.classList.remove('selected'));

      const resetMap = {
        'filterMonth': this.formatMonthLabel(defaultM),
        'filterMTMType': defaultT,
        'filterBranch': 'Semua Cabang',
        'filterAlias': 'Semua Alias',
        'filterBrandGroup': 'Semua Grup Brand',
        'filterItem': 'Semua Produk / Item',
        'filterReason': 'Semua Alasan'
      };

      Object.entries(resetMap).forEach(([id, text]) => {
        const select = document.getElementById(id);
        const container = select?.closest('.custom-select-container');
        if (container) {
          const txtEl = container.querySelector('.custom-select-text');
          if (txtEl) txtEl.textContent = text;
        }
      });

      this.updateCrossFilterBadge();
      this.updateCascadingDropdowns();
      this.refreshDashboardData();
    });

    // Pareto Mode strictly defaults to Unfulfill Problem Analysis
    this.isParetoUnfulfill = true;


    // Pareto Tabs
    const tabs = document.querySelectorAll('.pareto-tab');
    tabs.forEach(t => {
      t.addEventListener('click', (e) => {
        tabs.forEach(x => x.classList.remove('active'));
        const target = e.target;
        target.classList.add('active');
        this.activeParetoDimension = target.getAttribute('data-dim') || 'alasan';
        this.fetchParetoData();
        this.fetchGridData();
      });
    });

    // Window Resize Handler for Treemap Responsiveness
    window.addEventListener('resize', () => {
      if (this.lastParetoItems && this.lastParetoItems.length > 0) {
        this.renderParetoTreeMaps(this.lastParetoItems);
      }
    });



    // PPT Export Options Modal Setup
    const btnOpenExport = document.getElementById('btnOpenExportModal');
    const exportPPTModal = document.getElementById('exportPPTModal');
    const btnCloseExport = document.getElementById('btnCloseExportModal');
    const btnCancelExport = document.getElementById('btnCancelExportModal');
    const btnConfirmExport = document.getElementById('btnConfirmExportPPT');
    const btnSelectAllExportMonths = document.getElementById('btnSelectAllExportMonths');
    const btnResetExportMonths = document.getElementById('btnResetExportMonths');

    // Open Export Modal
    btnOpenExport?.addEventListener('click', () => {
      if (exportPPTModal) {
        this.renderExportMonthGrid();
        exportPPTModal.style.display = 'flex';
      }
    });

    // Close Export Modal
    const closeExportModal = () => {
      if (exportPPTModal) exportPPTModal.style.display = 'none';
    };
    btnCloseExport?.addEventListener('click', closeExportModal);
    btnCancelExport?.addEventListener('click', closeExportModal);
    exportPPTModal?.addEventListener('click', (e) => {
      if (e.target === exportPPTModal) closeExportModal();
    });

    // Select All / Reset Month Checkboxes
    btnSelectAllExportMonths?.addEventListener('click', () => {
      const checkboxes = document.querySelectorAll('#exportMonthGrid input[type="checkbox"]');
      checkboxes.forEach(cb => {
        cb.checked = true;
        cb.closest('.export-month-card')?.classList.add('selected');
      });
    });

    btnResetExportMonths?.addEventListener('click', () => {
      const activeMonth = this.activeFilters.month || this.latestMonthDefault || '2026-08';
      const checkboxes = document.querySelectorAll('#exportMonthGrid input[type="checkbox"]');
      checkboxes.forEach(cb => {
        const isMatch = cb.value === activeMonth;
        cb.checked = isMatch;
        const card = cb.closest('.export-month-card');
        if (isMatch) card?.classList.add('selected');
        else card?.classList.remove('selected');
      });
    });

    // Confirm Export PPT Action
    btnConfirmExport?.addEventListener('click', async () => {
      const checkedBoxes = Array.from(document.querySelectorAll('#exportMonthGrid input[type="checkbox"]:checked'));
      if (checkedBoxes.length === 0) {
        alert('Silakan pilih minimal 1 bulan untuk dicetak ke laporan PPT.');
        return;
      }

      // Collect selected months and sort chronologically ascending (e.g. 2026-07 then 2026-08)
      const selectedMonths = checkedBoxes.map(cb => cb.value).sort();

      const originalText = btnConfirmExport.textContent;
      btnConfirmExport.disabled = true;
      btnConfirmExport.textContent = '⏳ Mencetak PPT...';

      try {
        const payload = {
          ...this.activeFilters,
          months: selectedMonths,
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

        if (!res.ok) throw new Error('Gagal mengunduh file PPT dari server.');

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const monthLabelStr = selectedMonths.length === 1 ? selectedMonths[0] : `${selectedMonths[0]}_sd_${selectedMonths[selectedMonths.length - 1]}`;
        a.download = `Laporan_Service_Level_MTM_${monthLabelStr}.pptx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        closeExportModal();
      } catch (err) {
        alert(err.message || 'Gagal ekspor PPT.');
      } finally {
        btnConfirmExport.disabled = false;
        btnConfirmExport.textContent = originalText;
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
      const monthInput = document.getElementById('uploadDeliveryMonth');
      if (monthInput) {
        let activeM = this.activeFilters.month;
        if (!activeM || !/^\d{4}-\d{2}$/.test(activeM)) {
          activeM = '2026-08';
        }
        monthInput.value = activeM;
      }
      const passInput = document.getElementById('uploadPasswordInput');
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
      const monthInput = document.getElementById('uploadDeliveryMonth');
      const fileInput = document.getElementById('datasetFileInput');
      const passInput = document.getElementById('uploadPasswordInput');
      const statusMsg = document.getElementById('uploadStatusMsg');
      const btnConfirm = document.getElementById('btnConfirmUpload');

      const progressWrapper = document.getElementById('uploadProgressWrapper');
      const progressStage = document.getElementById('uploadProgressStage');
      const progressPercent = document.getElementById('uploadProgressPercent');
      const progressBar = document.getElementById('uploadProgressBar');

      const updateProgress = (percent, stageText, isError = false, isSuccess = false) => {
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

      const periodeInput = document.getElementById('uploadPeriodeInput');
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

      let simulatedInterval = null;
      try {
        const formData = new FormData();
        formData.append('target_year', targetYear);
        formData.append('target_month_num', targetMonthVal);
        formData.append('target_month', targetMonth);
        formData.append('password', uploadPassword);
        formData.append('file', file);

        const url = `${this.apiBaseUrl}/api/data/upload?target_month=${encodeURIComponent(targetMonth)}&target_year=${encodeURIComponent(targetYear)}&target_month_num=${encodeURIComponent(targetMonthVal)}`;
        
        const uploadResult = await new Promise((resolve, reject) => {
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

          xhr.timeout = 180000;
          xhr.ontimeout = () => {
            if (simulatedInterval) clearInterval(simulatedInterval);
            reject(new Error('Waktu pengunggahan habis (Timeout 3 min). Silakan gunakan tombol Fast-Sync File Server di bawah.'));
          };

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
      } catch (err) {
        if (simulatedInterval) clearInterval(simulatedInterval);
        updateProgress(100, `❌ Gagal: ${err.message}`, true, false);
        if (statusMsg) {
          statusMsg.style.display = 'block';
          statusMsg.style.background = 'rgba(239, 68, 68, 0.18)';
          statusMsg.style.border = '1px solid #EF4444';
          statusMsg.style.color = '#FCA5A5';
          statusMsg.innerHTML = `❌ <strong>Gagal:</strong> ${err.message}`;
        }
      } finally {
        if (btnConfirm) {
          btnConfirm.disabled = false;
          btnConfirm.textContent = '⚡ Upload & Update Data Periode';
        }
      }
    });

    const btnLocalImport = document.getElementById('btnLocalImport');
    btnLocalImport?.addEventListener('click', async () => {
      const periodeInput = document.getElementById('uploadPeriodeInput');
      const targetMonth = periodeInput ? periodeInput.value.trim() : '2026-08';
      const passInput = document.getElementById('uploadPasswordInput');
      const uploadPassword = passInput ? passInput.value.trim() : '';

      if (!uploadPassword) {
        alert('Harap masukkan Password Akses Upload (Adelle@0403)');
        return;
      }

      try {
        btnLocalImport.disabled = true;
        btnLocalImport.textContent = '🚀 Memproses Fast-Sync...';
        const res = await fetch(`/api/data/import-local?target_month=${targetMonth}&password=${encodeURIComponent(uploadPassword)}`, {
          method: 'POST'
        });
        const json = await res.json();
        if (res.ok && json.status === 'success') {
          alert(`✅ Fast-Sync Sukses (0.1s)!\n${json.message}`);
          const uploadModal = document.getElementById('uploadModal');
          if (uploadModal) uploadModal.style.display = 'none';
          this.activeFilters.month = targetMonth;
          this.loadFilterOptions();
          this.refreshDashboardData();
        } else {
          alert(`❌ Fast-Sync Gagal: ${json.message}`);
        }
      } catch (err) {
        alert(`❌ Kesalahan: ${err.message}`);
      } finally {
        btnLocalImport.disabled = false;
        btnLocalImport.textContent = '🚀 Fast-Sync File Server (Opsi Kilat 0.1 Detik)';
      }
    });
  }

  updateUserUI() {
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

  async loadFilterOptions() {
    try {
      const res = await fetch(`${this.apiBaseUrl}/api/data/filters`);
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        const opts = json.data;
        this.latestMonthDefault = opts.latest_month || '2026-08';
        this.defaultMTMTypeDefault = opts.default_mtm_type || 'KA';

        const txtLastUpdate = document.getElementById('txtLastUpdateDB');
        if (txtLastUpdate && opts.last_update) {
          let formattedUpdate = opts.last_update;
          if (formattedUpdate.includes('/')) {
            const parts = formattedUpdate.split(' ')[0].split('/');
            if (parts.length >= 2) {
              formattedUpdate = `${parts[0]}/${parts[1]}`;
            }
          }
          txtLastUpdate.textContent = formattedUpdate;
        }

        // 1. Set active filters first so populateDropdown sees selected values
        this.availableMonths = opts.months || [];
        this.activeFilters.months = [this.latestMonthDefault];
        this.activeFilters.month = this.latestMonthDefault;
        this.activeFilters.mtm_types = [this.defaultMTMTypeDefault];
        this.activeFilters.mtm_type = this.defaultMTMTypeDefault;

        // 2. Populate dropdowns
        this.populateDropdown('filterMonth', opts.months, this.latestMonthDefault);
        this.populateDropdown('filterMTMType', opts.mtm_types, this.defaultMTMTypeDefault);
        this.populateDropdown('filterBranch', opts.branches);
        this.populateDropdown('filterAlias', opts.mtm_aliases);
        this.populateDropdown('filterBrandGroup', opts.brand_groups);
        this.populateDropdown('filterItem', opts.items);
        this.populateDropdown('filterReason', opts.reasons);

        // 3. Refresh dashboard data
        this.refreshDashboardData();
      }
    } catch (e) {
      console.warn('Backend API filter fetch fallback active', e);
      this.refreshDashboardData();
    }
  }

  renderExportMonthGrid() {
    const grid = document.getElementById('exportMonthGrid');
    if (!grid) return;

    const months = (this.availableMonths && this.availableMonths.length > 0)
      ? [...this.availableMonths].sort()
      : ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08'];

    const activeMonth = this.activeFilters.month || this.latestMonthDefault || '2026-08';

    const monthNames = {
      '01': 'JAN', '02': 'FEB', '03': 'MAR', '04': 'APR', '05': 'MEI', '06': 'JUN',
      '07': 'JUL', '08': 'AGU', '09': 'SEP', '10': 'OKT', '11': 'NOV', '12': 'DES'
    };

    grid.innerHTML = months.map(mStr => {
      const parts = String(mStr).split('-');
      const label = parts.length === 2 ? `${monthNames[parts[1]] || parts[1]}-${parts[0]}` : mStr;
      const isSelected = mStr === activeMonth;
      return `
        <label class="export-month-card ${isSelected ? 'selected' : ''}">
          <input type="checkbox" value="${mStr}" ${isSelected ? 'checked' : ''} onchange="this.closest('.export-month-card').classList.toggle('selected', this.checked)">
          <span>${label}</span>
        </label>
      `;
    }).join('');
  }

  async updateCascadingDropdowns() {
    if (this._isUpdatingCascading) return;
    this._isUpdatingCascading = true;

    try {
      const res = await fetch(`${this.apiBaseUrl}/api/data/filters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.activeFilters)
      });
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        const opts = json.data;
        const mapping = [
          { id: 'filterBranch', available: opts.branches, filterKey: 'branches' },
          { id: 'filterAlias', available: opts.mtm_aliases, filterKey: 'mtm_aliases' },
          { id: 'filterBrandGroup', available: opts.brand_groups, filterKey: 'brand_groups' },
          { id: 'filterItem', available: opts.items, filterKey: 'items' },
          { id: 'filterReason', available: opts.reasons, filterKey: 'reasons' },
          { id: 'filterMTMType', available: opts.mtm_types, filterKey: 'mtm_types' }
        ];

        mapping.forEach(({ id, available, filterKey }) => {
          this.repopulateCascadingOptions(id, available, filterKey);
        });
      }
    } catch (e) {
      console.warn('Cascading dropdown update error', e);
    } finally {
      this._isUpdatingCascading = false;
    }
  }

  repopulateCascadingOptions(id, availableItems, filterKey) {
    const select = document.getElementById(id);
    const container = select?.closest('.custom-select-container');
    const optionsList = container?.querySelector('.custom-options-list');
    if (!optionsList || !availableItems) return;

    let activeList = this.activeFilters[filterKey] || [];
    const activeSet = new Set(activeList);

    if (activeList.length > 0) return;

    const labelMap = {
      'filterMTMType': 'Semua Jenis MTM',
      'filterBranch': 'Semua Cabang',
      'filterAlias': 'Semua Alias',
      'filterBrandGroup': 'Semua Grup Brand',
      'filterItem': 'Semua Produk / Item',
      'filterReason': 'Semua Alasan'
    };
    const textEl = container?.querySelector('.custom-select-text');

    const updateDisplayAndFilters = () => {
      const checkedBoxes = Array.from(optionsList.querySelectorAll('.custom-option-checkbox:checked'));
      const checkedVals = checkedBoxes.map(cb => cb.value);
      this.activeFilters[filterKey] = checkedVals;

      if (id === 'filterMTMType') {
        this.activeFilters.mtm_type = checkedVals.length === 1 ? checkedVals[0] : (checkedVals.length > 1 ? 'ALL' : '');
      }

      if (textEl) {
        if (checkedVals.length === 0) textEl.textContent = labelMap[id] || 'Semua';
        else if (checkedVals.length === 1) textEl.textContent = checkedVals[0];
        else textEl.textContent = `${checkedVals.length} Terpilih`;
      }

      this.updateCascadingDropdowns();
      this.refreshDashboardData();
    };

    optionsList.innerHTML = '';

    const actionsBar = document.createElement('div');
    actionsBar.className = 'custom-actions-bar';
    actionsBar.innerHTML = `
      <span class="custom-action-link act-select-all">✓ Pilih Semua</span>
      <span class="custom-action-link act-clear">✕ Bersihkan</span>
    `;
    optionsList.appendChild(actionsBar);

    actionsBar.querySelector('.act-select-all').addEventListener('click', (e) => {
      e.stopPropagation();
      optionsList.querySelectorAll('.custom-option-checkbox').forEach(cb => cb.checked = true);
      updateDisplayAndFilters();
    });

    actionsBar.querySelector('.act-clear').addEventListener('click', (e) => {
      e.stopPropagation();
      optionsList.querySelectorAll('.custom-option-checkbox').forEach(cb => cb.checked = false);
      updateDisplayAndFilters();
    });

    if (select) select.innerHTML = '';

    availableItems.forEach(it => {
      const opt = document.createElement('option');
      opt.value = it;
      opt.textContent = it;
      if (activeSet.has(it)) opt.selected = true;
      if (select) select.appendChild(opt);

      const divOpt = document.createElement('div');
      divOpt.className = 'custom-option';

      const chk = document.createElement('input');
      chk.type = 'checkbox';
      chk.className = 'custom-option-checkbox';
      chk.value = it;
      chk.checked = activeSet.has(it);

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

      optionsList.appendChild(divOpt);
    });
  }

  populateDropdown(id, items, defaultVal) {
    const select = document.getElementById(id);
    if (!select) return;

    select.innerHTML = '';
    const container = select.closest('.custom-select-container');
    const textEl = container?.querySelector('.custom-select-text');
    const optionsList = container?.querySelector('.custom-options-list');

    if (!optionsList) return;
    optionsList.innerHTML = '';

    const labelMap = {
      'filterMonth': 'Pilih Bulan',
      'filterMTMType': 'Semua Jenis MTM',
      'filterBranch': 'Semua Cabang',
      'filterAlias': 'Semua Alias',
      'filterBrandGroup': 'Semua Grup Brand',
      'filterItem': 'Semua Produk / Item',
      'filterReason': 'Semua Alasan'
    };

    const keyMap = {
      'filterMonth': 'months',
      'filterMTMType': 'mtm_types',
      'filterBranch': 'branches',
      'filterAlias': 'mtm_aliases',
      'filterBrandGroup': 'brand_groups',
      'filterItem': 'items',
      'filterReason': 'reasons'
    };

    const targetKey = keyMap[id];
    let selectedValues = this.activeFilters[targetKey] || [];
    if (defaultVal && selectedValues.length === 0 && (id === 'filterMonth' || id === 'filterMTMType')) {
      selectedValues = [defaultVal];
      this.activeFilters[targetKey] = selectedValues;
      if (id === 'filterMonth') this.activeFilters.month = defaultVal;
      if (id === 'filterMTMType') this.activeFilters.mtm_type = defaultVal;
    }

    const isSingleMonth = (id === 'filterMonth');

    const updateDisplayAndFilters = () => {
      if (isSingleMonth) return;
      const checkedBoxes = Array.from(optionsList.querySelectorAll('.custom-option-checkbox:checked'));
      const checkedVals = checkedBoxes.map(cb => cb.value);
      this.activeFilters[targetKey] = checkedVals;

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
      this.updateCascadingDropdowns();
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

      actionsBar.querySelector('.act-select-all').addEventListener('click', (e) => {
        e.stopPropagation();
        optionsList.querySelectorAll('.custom-option-checkbox').forEach(cb => cb.checked = true);
        updateDisplayAndFilters();
      });

      actionsBar.querySelector('.act-clear').addEventListener('click', (e) => {
        e.stopPropagation();
        optionsList.querySelectorAll('.custom-option-checkbox').forEach(cb => cb.checked = false);
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
        span.textContent = this.formatMonthLabel(it);
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
            if (textEl) textEl.textContent = this.formatMonthLabel(it);
          }
          container.classList.remove('open');
          this.updateCascadingDropdowns();
          this.refreshDashboardData();
        });
      } else {
        const chk = document.createElement('input');
        chk.type = 'checkbox';
        chk.className = 'custom-option-checkbox';
        chk.value = it;
        chk.checked = selectedValues.includes(it);

        const span = document.createElement('span');
        span.textContent = (id === 'filterMonth') ? this.formatMonthLabel(it) : it;

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
        textEl.textContent = (selectedValues.length === 1 ? this.formatMonthLabel(selectedValues[0]) : (selectedValues.length > 1 ? `${selectedValues.length} Terpilih` : 'Semua Bulan'));
      } else {
        if (selectedValues.length === 0) {
          textEl.textContent = labelMap[id];
        } else if (selectedValues.length === 1) {
          textEl.textContent = (id === 'filterMonth') ? this.formatMonthLabel(selectedValues[0]) : selectedValues[0];
        } else {
          textEl.textContent = `${selectedValues.length} Terpilih`;
        }
      }
    }

  }

  getEffectiveFilters() {
    const filters = { ...this.activeFilters };
    if (this.treemapCrossFilter && this.treemapCrossFilter.name) {
      const dim = this.treemapCrossFilter.dimension;
      const val = this.treemapCrossFilter.name;
      if (dim === 'alasan') filters.reason = val;
      else if (dim === 'cabang') filters.branches = [val];
      else if (dim === 'mtm_alias') filters.mtm_aliases = [val];
      else if (dim === 'grup_brand') filters.brand_groups = [val];
      else if (dim === 'item') filters.items = [val];
    }
    return filters;
  }

  refreshDashboardData() {
    this.fetchKPIData();
    this.fetchTrendData();
    this.fetchParetoData();
    this.fetchGridData();
  }

  async fetchKPIData() {
    try {
      const res = await fetch(`${this.apiBaseUrl}/api/analytics/kpi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.getEffectiveFilters())
      });
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        const kpi = json.data;
        this.renderScorecard(kpi);
      }
    } catch (e) {
      console.warn('KPI fetch error', e);
    }
  }

  formatMetricVal(val, type) {
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

  renderScorecard(kpi) {
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





  async fetchTrendData() {
    try {
      const btnKirim = document.getElementById('btnTrendSLKirim');
      const activeTrendMetric = (btnKirim && btnKirim.classList.contains('active')) ? 'sl_kirim' : 'sl_realisasi';

      const res = await fetch(`${this.apiBaseUrl}/api/analytics/trend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.getEffectiveFilters())
      });
      const json = await res.json();
      if (res.ok && json.status === 'success') {
        this.renderMonthlyTrendChart(json.data, activeTrendMetric);
      }
    } catch (e) {
      console.warn('Trend fetch error', e);
    }
  }

  formatMonthLabel(monthStr) {
    if (!monthStr || monthStr === 'Semua Bulan' || monthStr === 'ALL') return monthStr;
    const parts = String(monthStr).trim().split('-');
    if (parts.length === 2) {
      const yr = parts[0];
      const mo = parts[1];
      const monthMap = {
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

  renderMonthlyTrendChart(trendList, metricKey) {
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





  async fetchParetoData() {
    try {
      const payload = {
        ...this.getEffectiveFilters(),
        metric_type: this.activeFilters.metric_type || 'idr',
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


  squarifyLayout(items, width, height) {
    const totalVal = items.reduce((s, it) => s + (it.value || 0), 0);
    if (totalVal <= 0 || width <= 0 || height <= 0) return [];

    const totalArea = width * height;
    const children = items.map(it => ({
      raw: it,
      area: ((it.value || 0) / totalVal) * totalArea
    }));

    const rects = [];

    const worstAspectRatio = (row, sideLen) => {
      if (!row.length || sideLen <= 0) return Infinity;
      const rowArea = row.reduce((s, c) => s + c.area, 0);
      if (rowArea <= 0) return Infinity;
      let maxA = 0;
      let minA = Infinity;
      for (let i = 0; i < row.length; i++) {
        if (row[i].area > maxA) maxA = row[i].area;
        if (row[i].area < minA) minA = row[i].area;
      }
      const s2 = sideLen * sideLen;
      const a2 = rowArea * rowArea;
      return Math.max((s2 * maxA) / a2, a2 / (s2 * minA));
    };

    const layoutRow = (row, container) => {
      const rowArea = row.reduce((s, c) => s + c.area, 0);
      const isHorizontal = container.w >= container.h;
      const sideLen = isHorizontal ? container.h : container.w;
      const rowThickness = sideLen > 0 ? rowArea / sideLen : 0;

      let currentOffset = isHorizontal ? container.y : container.x;

      row.forEach(c => {
        const itemLen = rowThickness > 0 ? c.area / rowThickness : 0;
        let rect;
        if (isHorizontal) {
          rect = {
            item: c.raw,
            x: container.x,
            y: currentOffset,
            w: rowThickness,
            h: itemLen
          };
          currentOffset += itemLen;
        } else {
          rect = {
            item: c.raw,
            x: currentOffset,
            y: container.y,
            w: itemLen,
            h: rowThickness
          };
          currentOffset += itemLen;
        }
        rects.push(rect);
      });

      if (isHorizontal) {
        container.x += rowThickness;
        container.w -= rowThickness;
      } else {
        container.y += rowThickness;
        container.h -= rowThickness;
      }
    };

    let container = { x: 0, y: 0, w: width, h: height };
    let currentRow = [];

    for (let i = 0; i < children.length; i++) {
      const c = children[i];
      const sideLen = Math.min(container.w, container.h);
      if (sideLen <= 0) break;

      if (currentRow.length === 0) {
        currentRow.push(c);
      } else {
        const currentWorst = worstAspectRatio(currentRow, sideLen);
        const newWorst = worstAspectRatio([...currentRow, c], sideLen);

        if (newWorst <= currentWorst) {
          currentRow.push(c);
        } else {
          layoutRow(currentRow, container);
          currentRow = [c];
        }
      }
    }

    if (currentRow.length > 0 && container.w > 0 && container.h > 0) {
      layoutRow(currentRow, container);
    }

    return rects;
  }

  getTreemapTileStyle(item, index, totalItems, vitalCutoff) {
    const isVital = index <= vitalCutoff;

    const mainPalettes = [
      // 0: Deep Imperial Navy Blue (#1 Dominan)
      { bg: 'linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%)', text: '#ffffff', valText: '#fde047', subText: '#cbd5e1', border: '1.5px solid #60a5fa' },
      // 1: Vibrant Royal Blue (#2)
      { bg: 'linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%)', text: '#ffffff', valText: '#ffffff', subText: '#e2e8f0', border: '1.5px solid #93c5fd' },
      // 2: Warm Vibrant Orange (#3 - High Contrast Accent)
      { bg: 'linear-gradient(135deg, #c2410c 0%, #ea580c 100%)', text: '#ffffff', valText: '#fde047', subText: '#ffedd5', border: '1.5px solid #fdba74' },
      // 3: Ice Turquoise Blue (#4)
      { bg: 'linear-gradient(135deg, #0284c7 0%, #38bdf8 100%)', text: '#ffffff', valText: '#fde047', subText: '#e0f2fe', border: '1.5px solid #bae6fd' },
      // 4: Golden Amber (#5)
      { bg: 'linear-gradient(135deg, #b45309 0%, #d97706 100%)', text: '#ffffff', valText: '#ffffff', subText: '#fef3c7', border: '1.5px solid #fde047' },
      // 5: Rich Indigo Violet (#6)
      { bg: 'linear-gradient(135deg, #3730a3 0%, #4f46e5 100%)', text: '#ffffff', valText: '#fde047', subText: '#e0e7ff', border: '1.5px solid #a5b4fc' },
      // 6: Emerald Teal (#7)
      { bg: 'linear-gradient(135deg, #0f766e 0%, #0d9488 100%)', text: '#ffffff', valText: '#99f6e4', subText: '#ccfbf1', border: '1.5px solid #5eead4' },
      // 7: Crimson Coral (#8)
      { bg: 'linear-gradient(135deg, #9f1239 0%, #e11d48 100%)', text: '#ffffff', valText: '#fecdd3', subText: '#ffe4e6', border: '1.5px solid #fda4af' },
      // 8: Steel Slate (#9)
      { bg: 'linear-gradient(135deg, #1e293b 0%, #475569 100%)', text: '#ffffff', valText: '#fde047', subText: '#cbd5e1', border: '1.5px solid #94a3b8' }
    ];

    const minorPalettes = [
      { bg: 'linear-gradient(135deg, #fdba74 0%, #fed7aa 100%)', text: '#7c2d12', valText: '#7c2d12', subText: 'rgba(124, 45, 18, 0.85)', border: '1.5px solid #ffffff' },
      { bg: 'linear-gradient(135deg, #cbd5e1 0%, #e2e8f0 100%)', text: '#1e293b', valText: '#0f172a', subText: 'rgba(30, 41, 59, 0.85)', border: '1.5px solid #ffffff' },
      { bg: 'linear-gradient(135deg, #a5f3fc 0%, #bae6fd 100%)', text: '#0369a1', valText: '#0369a1', subText: 'rgba(3, 105, 161, 0.85)', border: '1.5px solid #ffffff' },
      { bg: 'linear-gradient(135deg, #ddd6fe 0%, #ede9fe 100%)', text: '#4c1d95', valText: '#4c1d95', subText: 'rgba(76, 29, 149, 0.85)', border: '1.5px solid #ffffff' },
      { bg: 'linear-gradient(135deg, #fef08a 0%, #fef9c3 100%)', text: '#713f12', valText: '#713f12', subText: 'rgba(113, 63, 18, 0.85)', border: '1.5px solid #ffffff' }
    ];

    if (index < mainPalettes.length) {
      return mainPalettes[index];
    } else if (isVital) {
      return mainPalettes[1 + ((index - mainPalettes.length) % (mainPalettes.length - 1))];
    } else {
      return minorPalettes[index % minorPalettes.length];
    }
  }

  showTreemapTooltip(e, item, isVital, valStr) {
    let tooltip = document.getElementById('treemapTooltip');
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.id = 'treemapTooltip';
      tooltip.style.cssText = `
        position: fixed;
        display: none;
        pointer-events: none;
        z-index: 99999;
        background: rgba(15, 23, 42, 0.96);
        border: 1px solid rgba(245, 158, 11, 0.7);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.7);
        color: #ffffff;
        padding: 0.65rem 0.95rem;
        border-radius: 8px;
        font-size: 0.8rem;
        backdrop-filter: blur(12px);
        transition: opacity 0.1s ease;
      `;
      document.body.appendChild(tooltip);
    }

    tooltip.style.display = 'block';
    tooltip.style.left = Math.min(window.innerWidth - 250, e.clientX + 14) + 'px';
    tooltip.style.top = Math.min(window.innerHeight - 150, e.clientY + 14) + 'px';
    const slKirimVal = item.sl_kirim !== undefined ? item.sl_kirim.toFixed(1) + '%' : '-';
    const slRealVal = item.sl_realisasi !== undefined ? item.sl_realisasi.toFixed(1) + '%' : '-';

    tooltip.innerHTML = `
      <div style="font-weight:800; font-size:0.88rem; color:#fde047; margin-bottom:0.3rem; border-bottom:1px solid rgba(255,255,255,0.15); padding-bottom:0.25rem;">${item.name}</div>
      <div style="color:#e2e8f0; margin-bottom:0.15rem;">Nilai: <strong style="color:#ffffff;">${valStr}</strong></div>
      <div style="color:#cbd5e1; margin-bottom:0.15rem;">Kontribusi: <strong style="color:#60a5fa;">${item.percentage.toFixed(1)}%</strong></div>
      <div style="color:#cbd5e1; margin-bottom:0.15rem;">Kumulatif: <strong>${item.cumulative_percentage.toFixed(1)}%</strong></div>
      <div style="color:#cbd5e1; margin-bottom:0.25rem;">SL Kirim: <strong style="color:#4ade80;">${slKirimVal}</strong> | SL Terima: <strong style="color:#fbbf24;">${slRealVal}</strong></div>
      <div>${isVital ? '<span style="color:#fde047; font-weight:700; background:rgba(234,179,8,0.25); border:1px solid rgba(234,179,8,0.5); padding:0.1rem 0.4rem; border-radius:4px; font-size:0.72rem;">⭐ Pareto 80%</span>' : '<span style="color:#94a3b8; background:rgba(255,255,255,0.08); padding:0.1rem 0.4rem; border-radius:4px; font-size:0.72rem;">Minor (<20%)</span>'}</div>
    `;
  }

  hideTreemapTooltip() {
    const tooltip = document.getElementById('treemapTooltip');
    if (tooltip) tooltip.style.display = 'none';
  }

  renderParetoTreeMaps(items) {
    const container = document.getElementById('treemapGrid');
    if (!container) return;

    const nonZeroItems = (items || []).filter(it => it.value > 0);
    this.lastParetoItems = nonZeroItems;

    if (!nonZeroItems || nonZeroItems.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); padding: 1.5rem;">Tidak ada data Tree Maps untuk kombinasi filter ini.</div>';
      return;
    }

    container.innerHTML = '';
    const metricType = this.activeFilters.metric_type || 'idr';

    let vitalIndexCutoff = 0;
    for (let i = 0; i < nonZeroItems.length; i++) {
      vitalIndexCutoff = i;
      if (nonZeroItems[i].cumulative_percentage >= 80.0) {
        break;
      }
    }

    // Display items (up to top 60 items so even small tail items render at bottom right)
    const displayItems = nonZeroItems.slice(0, 60);

    const execWrap = document.createElement('div');
    execWrap.className = 'tableau-executive-treemap';

    const canvasWrapper = document.createElement('div');
    canvasWrapper.className = 'treemap-canvas-wrapper';
    execWrap.appendChild(canvasWrapper);
    container.appendChild(execWrap);

    // Calculate squarify layout
    const cWidth = canvasWrapper.clientWidth || 1000;
    const cHeight = canvasWrapper.clientHeight || 530;

    const rects = this.squarifyLayout(displayItems, cWidth, cHeight);

    rects.forEach((rect, idx) => {
      const it = rect.item;
      const isVital = idx <= vitalIndexCutoff;
      const style = this.getTreemapTileStyle(it, idx, displayItems.length, vitalIndexCutoff);

      const isSelected = (
        this.treemapCrossFilter &&
        this.treemapCrossFilter.dimension === this.activeParetoDimension &&
        this.treemapCrossFilter.name === it.name
      );

      const valStr = this.formatMetricVal(it.value, metricType);
      const tile = document.createElement('div');
      tile.className = 'tableau-tile' + (isSelected ? ' selected' : '');

      tile.style.cssText = `
        position: absolute;
        left: ${rect.x.toFixed(1)}px;
        top: ${rect.y.toFixed(1)}px;
        width: ${rect.w.toFixed(1)}px;
        height: ${rect.h.toFixed(1)}px;
        background: ${style.bg};
        color: ${style.text};
        border: ${style.border};
        box-sizing: border-box;
        overflow: hidden;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: ${rect.w > 75 && rect.h > 55 ? '7px 9px' : '3px 5px'};
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        z-index: ${isSelected ? '25' : '1'};
      `;

      let innerContent = '';
      const slLabel = it.sl_label || ((this.activeFilters.sl_type || 'sl_kirim') === 'sl_kirim' ? 'SL Kirim' : 'SL Terima');
      const slActiveVal = (it.sl_active !== undefined ? it.sl_active : ((this.activeFilters.sl_type || 'sl_kirim') === 'sl_kirim' ? it.sl_kirim : it.sl_realisasi));
      const slColor = slLabel === 'SL Kirim' ? '#4ade80' : '#fbbf24';

      if (rect.w >= 110 && rect.h >= 75) {
        const badgeHtml = isVital
          ? `<span style="font-size: 0.65rem; font-weight: 800; color: #fde047; background: rgba(0,0,0,0.6); border: 1.5px solid rgba(234,179,8,0.8); padding: 0.12rem 0.4rem; border-radius: 4px; float: right;">⭐ Pareto 80%</span>`
          : ``;
        const titleFontSize = isVital ? Math.min(17, Math.max(12, Math.floor(rect.w / 9.5))) : Math.min(15, Math.max(11, Math.floor(rect.w / 11)));
        const valFontSize = isVital ? Math.min(19, Math.max(14, Math.floor(rect.w / 7.5))) : Math.min(17, Math.max(12, Math.floor(rect.w / 9)));
        const subFontSize = isVital ? '10.5px' : '10px';

        innerContent = `
          <div>
            ${badgeHtml}
            <div style="font-size: ${titleFontSize}px; font-weight: 800; text-transform: uppercase; line-height: 1.2; word-break: break-word; color: ${style.text};">${it.name}</div>
          </div>
          <div style="margin-top: 0.2rem;">
            <div style="font-size: ${valFontSize}px; font-weight: 800; color: ${style.valText}; text-shadow: 0 1px 4px rgba(0,0,0,0.4);">${valStr}</div>
            <div style="font-size: ${subFontSize}; color: ${style.subText}; margin-top: 0.15rem; line-height: 1.3;">
              <div>Kontribusi: <strong>${it.percentage.toFixed(1)}%</strong> <span style="opacity:0.85;">(Kum: ${it.cumulative_percentage.toFixed(1)}%)</span></div>
              ${slActiveVal !== undefined ? `<div style="font-weight: 700; color: ${slColor}; margin-top: 1px;">${slLabel}: ${slActiveVal.toFixed(1)}%</div>` : ''}
            </div>
          </div>
        `;
      } else if (rect.w >= 70 && rect.h >= 45) {
        const titleFontSize = isVital ? Math.min(13, Math.max(10, Math.floor(rect.w / 7.5))) : Math.min(12, Math.max(9.5, Math.floor(rect.w / 8)));
        const valFontSize = isVital ? Math.min(14, Math.max(11, Math.floor(rect.w / 6.5))) : Math.min(13, Math.max(10, Math.floor(rect.w / 7)));

        innerContent = `
          <div>
            <div style="font-size: ${titleFontSize}px; font-weight: 800; text-transform: uppercase; line-height: 1.15; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: ${style.text};">${it.name}</div>
          </div>
          <div>
            <div style="font-size: ${valFontSize}px; font-weight: 800; color: ${style.valText};">${valStr}</div>
            <div style="font-size: 9.5px; color: ${style.subText}; margin-top: 1px;">
              ${it.percentage.toFixed(1)}% ${slActiveVal !== undefined ? `| <strong style="color:${slColor};">${slLabel}: ${slActiveVal.toFixed(1)}%</strong>` : ''}
            </div>
          </div>
        `;
      } else if (rect.w >= 45 && rect.h >= 28) {
        const shortName = it.name.length > 10 ? it.name.substring(0, 8) + '..' : it.name;
        innerContent = `
          <div style="font-size: ${Math.min(10.5, Math.max(8.5, Math.floor(rect.w / 6.5)))}px; font-weight: 700; text-transform: uppercase; line-height: 1.1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: ${style.text};">${shortName}</div>
          <div style="font-size: 8.5px; font-weight: 700; color: ${style.valText}; opacity: 0.9;">${it.percentage.toFixed(1)}%</div>
        `;
      } else {
        innerContent = '';
      }

      tile.innerHTML = innerContent;

      tile.addEventListener('mousemove', (e) => {
        this.showTreemapTooltip(e, it, isVital, valStr);
        tile.style.transform = 'scale(1.02)';
        tile.style.zIndex = '40';
        tile.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
      });
      tile.addEventListener('mouseleave', () => {
        this.hideTreemapTooltip();
        tile.style.transform = 'none';
        tile.style.zIndex = isSelected ? '25' : '1';
        tile.style.boxShadow = 'none';
      });

      tile.addEventListener('click', (e) => {
        e.stopPropagation();
        this.handleTreemapClick(it.name);
      });

      canvasWrapper.appendChild(tile);
    });

    this.updateCrossFilterBadge();
  }

  clearParetoCrossFilter() {
    if (this.treemapCrossFilter) {
      this.treemapCrossFilter = null;
      this.updateCrossFilterBadge();
      this.refreshDashboardData();
    }
  }

  updateCrossFilterBadge() {
    const badge = document.getElementById('crossFilterBadge');
    if (!badge) return;

    if (this.treemapCrossFilter && this.treemapCrossFilter.name) {
      badge.style.background = 'rgba(234, 179, 8, 0.2)';
      badge.style.borderColor = '#EAB308';
      badge.style.color = '#FDE047';
      badge.innerHTML = `🔍 Treemap Cross-Filter: <strong>${this.treemapCrossFilter.name}</strong> <button id="btnResetTreemapFilter" style="margin-left: 8px; background: #DC2626; color: white; border: none; padding: 3px 10px; border-radius: 4px; cursor: pointer; font-size: 0.75rem; font-weight: 700; box-shadow: 0 2px 6px rgba(0,0,0,0.4);">✕ Lepas Filter Treemap</button>`;
      badge.style.cursor = 'default';
      badge.onclick = null;

      const btnReset = badge.querySelector('#btnResetTreemapFilter');
      btnReset?.addEventListener('click', (e) => {
        e.stopPropagation();
        this.clearParetoCrossFilter();
      });
    } else {
      badge.style.background = 'rgba(255, 255, 255, 0.05)';
      badge.style.borderColor = 'rgba(255, 255, 255, 0.1)';
      badge.style.color = 'var(--text-muted)';
      badge.innerHTML = 'Klik kotak Treemap untuk Cross-Filter';
      badge.style.cursor = 'default';
      badge.onclick = null;
    }
  }

  handleTreemapClick(itemName) {
    if (this.treemapCrossFilter && this.treemapCrossFilter.dimension === this.activeParetoDimension && this.treemapCrossFilter.name === itemName) {
      this.treemapCrossFilter = null;
    } else {
      this.treemapCrossFilter = {
        dimension: this.activeParetoDimension,
        name: itemName
      };
    }
    this.updateCrossFilterBadge();
    this.refreshDashboardData();
  }

  async fetchGridData() {
    try {
      const payload = {
        ...this.getEffectiveFilters(),
        metric_type: this.activeFilters.metric_type || 'idr',
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

  renderDetailGrid(records) {
    const tbody = document.getElementById('gridTbody');
    const badge = document.getElementById('gridCountBadge');
    const titleEl = document.getElementById('gridTableTitle');
    const thDimEl = document.getElementById('thDimName');

    const dimLabelMap = {
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

    const thGapHeader = document.getElementById('thGapHeader');
    const isKirim = (this.activeFilters.sl_type || 'sl_kirim') === 'sl_kirim';
    if (thGapHeader) {
      thGapHeader.textContent = isKirim ? 'Gap Unfulfilled (Pesan - Kirim)' : 'Gap Unfulfilled (Pesan - Realisasi)';
    }

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
        ? `<span style="font-size: 0.7rem; font-weight: 700; color: #FDE047; background: rgba(220,38,38,0.25); border: 1px solid #F87171; padding: 0.15rem 0.45rem; border-radius: 4px;">⭐ Pareto 80%</span>`
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

if (document.readyState === 'loading') {
  window.addEventListener('DOMContentLoaded', () => new DashboardApp());
} else {
  new DashboardApp();
}
