document.addEventListener('DOMContentLoaded', () => {
    const decodeForm = document.getElementById('decode-form');
    const serialInput = document.getElementById('serial-input');
    const decodeBtn = document.getElementById('decode-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');
    
    const welcomeMsg = document.getElementById('welcome-message');
    const visualizerContainer = document.getElementById('visualizer-container');
    const pinBlocks = document.getElementById('pin-blocks');
    const tooltipText = document.getElementById('tooltip-text');
    
    const specsEmpty = document.getElementById('specs-empty');
    const specsContent = document.getElementById('specs-content');
    const specMakeTitle = document.getElementById('spec-make-title');
    const specFormat = document.getElementById('spec-format');
    const specMake = document.getElementById('spec-make');
    const specModel = document.getElementById('spec-model');
    const specYear = document.getElementById('spec-year');
    const specPlant = document.getElementById('spec-plant');
    
    const confidenceCard = document.getElementById('decoding-confidence-card');
    const confIcon = document.getElementById('conf-icon');
    const confIconWrapper = document.getElementById('conf-icon-wrapper');
    const specConfDesc = document.getElementById('spec-conf-desc');
    
    const pricingEmpty = document.getElementById('pricing-empty');
    const pricingContent = document.getElementById('pricing-content');
    const pricingModelTitle = document.getElementById('pricing-model-title');
    const pricingRows = document.getElementById('pricing-rows');
    
    const sampleBadges = document.querySelectorAll('.sample-badge');

    // 1. Intercept Form Submission
    decodeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const serial = serialInput.value.trim();
        if (!serial) return;

        // Set Loading State
        setLoading(true);

        try {
            const response = await fetch(`/api/decode?serial=${encodeURIComponent(serial)}`);
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || 'Server error occurred during decoding');
            }
            const data = await response.json();
            renderDecodedResult(data);
        } catch (err) {
            alert(`Decoding Failed: ${err.message}`);
            console.error(err);
        } finally {
            setLoading(false);
        }
    });

    // 2. Click Sample Buttons
    sampleBadges.forEach(badge => {
        badge.addEventListener('click', () => {
            const serial = badge.getAttribute('data-serial');
            serialInput.value = serial;
            decodeForm.dispatchEvent(new Event('submit'));
        });
    });

    // 3. Set Loading UI State
    function setLoading(isLoading) {
        if (isLoading) {
            decodeBtn.disabled = true;
            serialInput.disabled = true;
            btnText.classList.add('hidden');
            btnLoader.classList.remove('hidden');
        } else {
            decodeBtn.disabled = false;
            serialInput.disabled = false;
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
        }
    }

    // 4. Render the Decoded Response Payload
    function renderDecodedResult(data) {
        // Toggle Layout Views
        welcomeMsg.classList.add('hidden');
        visualizerContainer.classList.remove('hidden');
        
        specsEmpty.classList.add('hidden');
        specsContent.classList.remove('hidden');
        
        pricingEmpty.classList.add('hidden');
        pricingContent.classList.remove('hidden');

        // Render Exploded PIN View
        pinBlocks.innerHTML = '';
        const defaultTooltip = "Hover or tap on any block above to inspect its structural logic and meaning.";
        tooltipText.textContent = defaultTooltip;

        if (data.breakdown && data.breakdown.length > 0) {
            data.breakdown.forEach(block => {
                // If it's an empty block (e.g. metadata year decoder), skip drawing it as a char block
                if (!block.chars) return;

                const blockEl = document.createElement('div');
                blockEl.className = `pin-block ${block.color || 'gray'}`;
                
                const charEl = document.createElement('span');
                charEl.className = 'char';
                charEl.textContent = block.chars;
                
                const labelEl = document.createElement('span');
                labelEl.className = 'label';
                labelEl.textContent = block.label;
                
                blockEl.appendChild(charEl);
                blockEl.appendChild(labelEl);
                
                // Tooltip events
                const updateTooltip = () => {
                    // Highlight current block
                    document.querySelectorAll('.pin-block').forEach(b => b.classList.remove('active'));
                    blockEl.classList.add('active');
                    tooltipText.innerHTML = `<strong>${block.label} (${block.chars}):</strong> ${block.desc}`;
                };

                const resetTooltip = () => {
                    blockEl.classList.remove('active');
                    tooltipText.textContent = defaultTooltip;
                };

                blockEl.addEventListener('mouseenter', updateTooltip);
                blockEl.addEventListener('mouseleave', resetTooltip);
                blockEl.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    updateTooltip();
                });

                pinBlocks.appendChild(blockEl);
            });
        }

        // Apply dynamic brand styling to the specifications panel
        const specsPanel = document.querySelector('.specs-panel');
        if (specsPanel) {
            specsPanel.className = 'panel glass specs-panel';
            if (data.make_key) {
                let brandClass = data.make_key.toLowerCase();
                if (brandClass.startsWith('agco')) {
                    brandClass = 'agco';
                }
                specsPanel.classList.add(`brand-${brandClass}`);
            }
        }

        // Fill Decoded Specification Cards
        specMakeTitle.textContent = data.make;
        specFormat.textContent = data.format;
        specMake.textContent = data.make;
        specModel.textContent = data.model !== "Unknown" ? data.model : "Model Prefix Matching";
        specYear.textContent = data.year ? data.year : "Sequence Range";
        specPlant.textContent = data.plant;

        // Customize Database Match Confidence Card
        if (data.year) {
            confidenceCard.className = "card note-card text-green";
            confIcon.className = "fa-solid fa-circle-check";
            confIconWrapper.className = "note-icon-wrapper text-green";
            specConfDesc.textContent = "Exact matching model range and production parameters mapped with high confidence.";
        } else {
            confidenceCard.className = "card note-card text-orange";
            confIcon.className = "fa-solid fa-circle-exclamation";
            confIconWrapper.className = "note-icon-wrapper text-orange";
            specConfDesc.textContent = "Make and plant structures decoded. Sequential range lookup suggested for precise manufacturing year.";
        }

        // Render Valuation Table
        pricingModelTitle.textContent = `${data.make} ${data.model !== "Unknown" ? data.model : "Series"}`;
        pricingRows.innerHTML = '';

        if (data.similar_sales && data.similar_sales.length > 0) {
            data.similar_sales.forEach(sale => {
                const tr = document.createElement('tr');
                
                const tdDate = document.createElement('td');
                tdDate.textContent = formatDate(sale.sold_date);
                
                const tdYear = document.createElement('td');
                tdYear.textContent = sale.year ? sale.year : "N/A";
                
                const tdSerial = document.createElement('td');
                tdSerial.textContent = sale.serial;
                
                const tdAuctioneer = document.createElement('td');
                tdAuctioneer.textContent = sale.auctioneer;
                
                const tdLoc = document.createElement('td');
                tdLoc.textContent = sale.state;
                
                const tdPrice = document.createElement('td');
                tdPrice.className = 'price text-right';
                tdPrice.textContent = `$${formatNumber(sale.price)}`;
                
                tr.appendChild(tdDate);
                tr.appendChild(tdYear);
                tr.appendChild(tdSerial);
                tr.appendChild(tdAuctioneer);
                tr.appendChild(tdLoc);
                tr.appendChild(tdPrice);
                
                pricingRows.appendChild(tr);
            });
        } else {
            const tr = document.createElement('tr');
            const tdEmpty = document.createElement('td');
            tdEmpty.colSpan = 6;
            tdEmpty.className = 'text-center';
            tdEmpty.style.padding = '2rem';
            tdEmpty.textContent = `No recent transaction listings found in the database matching model ${data.model}.`;
            tr.appendChild(tdEmpty);
            pricingRows.appendChild(tr);
        }
    }

    // Utilities
    function formatNumber(num) {
        if (num === null || num === undefined) return '-';
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    function formatDate(dateStr) {
        if (!dateStr || dateStr === 'Unknown') return 'Unknown';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        } catch {
            return dateStr;
        }
    }
});
