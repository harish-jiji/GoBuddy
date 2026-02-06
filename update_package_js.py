
path = r"c:\project\TOURISM\templates\admin\package_form.html"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# I will find the script block starting from renderItinerary and replace it till saveItineraryJSON or end of script
# The previous view_file confirms the content.

start_marker = "// --- RENDER LOGIC ---"
end_marker = "// Run"

new_js = """// --- RENDER LOGIC ---
    function renderItinerary() {
        const container = document.getElementById('daysContainer');
        if (!container) return;

        // Build all HTML
        let allDaysHtml = '';

        itineraryData.forEach((day, index) => {
            if (!day.items) day.items = [];
            if (!day.day) day.day = index + 1;

            const dayHtml = `
            <div class="day-section relative pl-8" data-day-index="${index}">
                <!-- Vertical Line -->
                <div class="absolute left-[3px] top-0 bottom-0 w-0.5 bg-white/10 timeline-connector"></div>
                <!-- Node -->
                <div class="absolute -left-[6px] top-0 w-5 h-5 bg-blue-500 border-4 border-[#0f172a] rounded-full z-10"></div>

                <div class="glass p-5 mb-12 border-l-4 border-blue-500">
                    <!-- HEADER -->
                    <div class="flex justify-between items-center mb-6 border-b border-white/5 pb-4">
                        <h2 class="text-2xl font-bold text-white flex items-center gap-3">
                            <span class="bg-blue-600/20 text-blue-400 text-sm px-3 py-1 rounded-full border border-blue-500/30">Day ${day.day}</span>
                            <span class="text-gray-300 text-lg">Itinerary</span>
                        </h2>
                        <div class="text-right">
                            <div class="text-xs text-gray-400 uppercase tracking-wider mb-1">Total Items</div>
                            <div class="text-xl font-bold text-white">${day.items.length}</div>
                        </div>
                    </div>

                    <!-- START LOCATION -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        <div>
                            <label class="text-[10px] text-green-400 uppercase font-bold mb-1 block">Start Location</label>
                            <input type="text" value="${day.start_location || ''}" 
                                class="w-full bg-black/20 border-b border-white/20 px-3 py-2 text-white outline-none focus:border-green-500 transition"
                                placeholder="Where does the day start?"
                                oninput="updateDayField(${index}, 'start_location', this.value)">
                        </div>
                        <div>
                            <label class="text-[10px] text-gray-400 uppercase font-bold mb-1 block">Start Time</label>
                            <input type="time" value="${day.start_time || '09:00'}"
                                class="w-full bg-black/20 border-b border-white/20 px-3 py-2 text-white outline-none focus:border-blue-500 transition"
                                onchange="updateDayField(${index}, 'start_time', this.value)">
                        </div>
                    </div>

                    <!-- ITEMS LIST -->
                    <div class="space-y-4 relative pl-6 mb-4">
                        <div class="absolute left-[10px] top-2 bottom-2 w-px bg-gray-700 bg-dashed"></div>
                        ${renderItems(day.items, index)}
                    </div>
                    
                    <!-- ADD BUTTONS -->
                    <div class="flex gap-2 mb-4">
                        <button type="button" onclick="addLocation(${index})"
                            class="flex-1 py-2 border-2 border-dashed border-gray-700 rounded-xl text-gray-400 hover:text-white hover:border-blue-500 hover:bg-blue-500/5 transition flex items-center justify-center gap-2 text-sm">
                            <i class="fas fa-map-marker-alt"></i> Add Location
                        </button>
                        <button type="button" onclick="addActivity(${index})"
                            class="flex-1 py-2 border-2 border-dashed border-gray-700 rounded-xl text-gray-400 hover:text-white hover:border-green-500 hover:bg-green-500/5 transition flex items-center justify-center gap-2 text-sm">
                            <i class="fas fa-plus"></i> Add Activity
                        </button>
                    </div>
                </div>
            </div>`;
            allDaysHtml += dayHtml;
        });

        container.innerHTML = allDaysHtml;
        calculateTotalCost();
    }

    function renderItems(items, dayIndex) {
        if (!items || items.length === 0) return '<div class="text-xs text-gray-500 italic pl-4">No items added. Add a location first, then activities.</div>';

        return items.map((item, itemIndex) => {
            const itemType = item.item_type || 'activity';

            if (itemType === 'location') {
                let destOptions = '<option value="">Select Destination</option>';
                if (TRIP_DESTINATIONS.length > 0) {
                    TRIP_DESTINATIONS.forEach(d => {
                        const safeName = (d.name || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                        destOptions += `<option value="${d.id}" ${item.destination_id == d.id ? 'selected' : ''}>${safeName}</option>`;
                    });
                }

                return `
                <div class="relative flex items-start gap-3 mb-4 group">
                    <div class="w-3 h-3 rounded-full bg-blue-500 mt-2 flex-shrink-0 shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
                    <div class="flex-1 bg-blue-500/10 border-l-2 border-blue-500 rounded-r-lg p-3">
                        <div class="flex justify-between mb-2">
                            <input type="text" value="${(item.name || '').replace(/"/g, '&quot;')}" placeholder="Location Name"
                                 class="bg-transparent font-semibold text-sm text-white border-b border-transparent focus:border-blue-500 outline-none w-3/4"
                                 oninput="updateItemField(${dayIndex}, ${itemIndex}, 'name', this.value)">
                            <button type="button" onclick="removeItem(${dayIndex}, ${itemIndex})" class="text-gray-500 hover:text-red-400"><i class="fas fa-times"></i></button>
                        </div>
                        <select class="w-full bg-black/40 border border-white/10 rounded px-2 py-1.5 text-xs text-white"
                                onchange="handleLocationSelect(${dayIndex}, ${itemIndex}, this.value)">
                            ${destOptions}
                        </select>
                    </div>
                </div>`;
            } else {
                // Activity
                const mainType = item.type || 'sightseeing';
                const subTypeOptions = getSubTypeOptions(mainType);
                const currentSubType = item.sub_type || '';

                // Generate sub-type select options
                let subTypeSelectHtml = `<select class="w-full bg-black/40 border border-white/10 rounded px-2 py-1.5 text-xs text-white"
                        onchange="updateItemField(${dayIndex}, ${itemIndex}, 'sub_type', this.value)">
                        <option value="">Select Detail</option>
                        ${subTypeOptions.map(opt => f'<option value="{opt["value"]}" {"selected" if currentSubType == opt["value"] else ""}>{opt["label"]}</option>').join('')}
                    </select>`; // Wait, f-string in python script, I need to escape curly braces or use .format or simple string concat. 
                
                // Correction: since I am writing JS code inside a Python string, I must be careful.
                // The JS code should be exactly as it is.
                
                return `
                <div class="relative flex items-start gap-3 mb-4 group">
                    <div class="w-2 h-2 rounded-full bg-green-400 mt-2 flex-shrink-0 shadow-[0_0_10px_rgba(74,222,128,0.5)]"></div>
                    <div class="flex-1 bg-white/5 border-l-2 border-green-400/30 rounded-r-lg p-3 hover:bg-white/10 transition">
                        <div class="flex justify-between mb-2">
                            <input type="text" value="${(item.name || '').replace(/"/g, '&quot;')}" placeholder="Activity Name"
                                 class="bg-transparent font-semibold text-sm text-white border-b border-transparent focus:border-green-500 outline-none w-3/4"
                                 oninput="updateItemField(${dayIndex}, ${itemIndex}, 'name', this.value)">
                            <button onclick="removeItem(${dayIndex}, ${itemIndex})" class="text-gray-500 hover:text-red-400"><i class="fas fa-times"></i></button>
                        </div>
                        <div class="grid grid-cols-12 gap-2">
                             <div class="col-span-3">
                                <label class="block text-[9px] uppercase text-gray-500">Type</label>
                                <select class="w-full bg-black/20 border border-white/10 rounded text-xs text-white py-1"
                                        onchange="updateItemField(${dayIndex}, ${itemIndex}, 'type', this.value); renderItinerary();">
                                    <option value="sightseeing" ${mainType == 'sightseeing' ? 'selected' : ''}>Sightseeing</option>
                                    <option value="travel" ${mainType == 'travel' ? 'selected' : ''}>Travel</option>
                                    <option value="food" ${mainType == 'food' ? 'selected' : ''}>Food</option>
                                    <option value="accommodation" ${mainType == 'accommodation' ? 'selected' : ''}>Accommodation</option>
                                    <option value="adventure" ${mainType == 'adventure' ? 'selected' : ''}>Adventure</option>
                                    <option value="shopping" ${mainType == 'shopping' ? 'selected' : ''}>Shopping</option>
                                </select>
                            </div>
                            <div class="col-span-3">
                                <label class="block text-[9px] uppercase text-gray-500">Sub-Type</label>
                                <select class="w-full bg-black/40 border border-white/10 rounded px-2 py-1.5 text-xs text-white"
                                     onchange="updateItemField(${dayIndex}, ${itemIndex}, 'sub_type', this.value)">
                                    <option value="">Select Detail</option>
                                    ${subTypeOptions.map(opt => `<option value="${opt.value}" ${currentSubType == opt.value ? 'selected' : ''}>${opt.label}</option>`).join('')}
                                </select>
                            </div>
                             <div class="col-span-3">
                                <label class="block text-[9px] uppercase text-gray-500">Time (hrs)</label>
                                <input type="number" value="${item.duration || 1}" min="0.5" step="0.5" 
                                    class="w-full bg-black/20 border border-white/10 rounded text-xs text-white py-1 pl-1"
                                    onchange="updateItemField(${dayIndex}, ${itemIndex}, 'duration', this.value)">
                            </div>
                            <div class="col-span-3">
                                <label class="block text-[9px] uppercase text-gray-500">Cost (₹)</label>
                                <input type="number" value="${item.cost || ''}" placeholder="0" min="0" 
                                    class="w-full bg-black/20 border border-white/10 rounded text-xs text-white py-1 pl-1"
                                    onchange="updateItemField(${dayIndex}, ${itemIndex}, 'cost', this.value)">
                            </div>
                        </div>
                    </div>
                </div>`;
            }
        }).join('');
    }

    // --- UPDATERS ---
    function updateDayField(dIdx, field, val) {
        itineraryData[dIdx][field] = val;
    }

    function updateItemField(dIdx, iIdx, field, val) {
        itineraryData[dIdx].items[iIdx][field] = val;
        
        if (field === 'type') {
            itineraryData[dIdx].items[iIdx].sub_type = ''; // Reset sub type
        }

        // Recalculate cost if field is cost
        if (field === 'cost') {
            calculateTotalCost();
        }
    }

    function addLocation(dIdx) {
        itineraryData[dIdx].items.push({
            item_type: 'location',
            name: '',
            destination_id: ''
        });
        renderItinerary();
    }

    function addActivity(dIdx) {
        itineraryData[dIdx].items.push({
            item_type: 'activity',
            name: '',
            type: 'sightseeing',
            sub_type: '',
            duration: 1,
            cost: ''
        });
        renderItinerary();
    }

    function removeItem(dIdx, iIdx) {
        itineraryData[dIdx].items.splice(iIdx, 1);
        renderItinerary();
        calculateTotalCost();
    }

    function handleLocationSelect(dIdx, iIdx, value) {
        const dest = TRIP_DESTINATIONS.find(d => d.id == value);
        if (dest) {
            itineraryData[dIdx].items[iIdx].name = dest.name;
            itineraryData[dIdx].items[iIdx].destination_id = value;
        } else {
             itineraryData[dIdx].items[iIdx].name = '';
             itineraryData[dIdx].items[iIdx].destination_id = '';
        }
        renderItinerary();
    }

    function calculateTotalCost() {
        let total = 0;
        if (itineraryData && Array.isArray(itineraryData)) {
            itineraryData.forEach(day => {
                if (day.items && Array.isArray(day.items)) {
                    day.items.forEach(item => {
                        if (item.cost) {
                            total += parseFloat(item.cost) || 0;
                        }
                    });
                }
            });
        }
        
        // Update Total Price field if it exists
        // Trying standard Django ID for total_cost field: id_total_cost by default, usually rendered as id_total_cost
        // But render_field might affect it. 
        // Based on Step 230: {% render_field form.total_cost ... %} usually produces id="id_total_cost".
        const costInput = document.getElementById('id_total_cost') || document.querySelector('[name="total_cost"]');
        if (costInput) {
            costInput.value = total;
        }
    }

    function saveItineraryJSON() {
        document.getElementById('itineraryJson').value = JSON.stringify(itineraryData);
        // Also ensure total cost is updated before submit
        calculateTotalCost();
        return true;
    }

    // --- MAIN INITIALIZATION ---
    """

if start_marker in content and end_marker in content:
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    new_content = content[:start_idx] + new_js + content[end_idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully replaced JS block.")
else:
    print("Could not find markers.")
