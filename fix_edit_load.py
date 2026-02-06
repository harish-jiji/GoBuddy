
path = r"c:\project\TOURISM\templates\admin\package_form.html"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Insert JSON script for existing itinerary
# Search for <input type="hidden" name="itinerary" id="itineraryJson">
marker = '<input type="hidden" name="itinerary" id="itineraryJson">'
if marker in content and 'id="server-itinerary-data"' not in content:
    replacement = marker + '\n' + """
        {% if object and object.itinerary %}
            {{ object.itinerary|json_script:"server-itinerary-data" }}
        {% endif %}
        {% if object %}
            <script id="server-destinations-data" type="application/json">
                [
                {% for d in object.destinations.all %}
                    {"id": {{ d.id }}, "name": "{{ d.name|escapejs }}"}{% if not forloop.last %},{% endif %}
                {% endfor %}
                ]
            </script>
        {% endif %}
    """
    content = content.replace(marker, replacement)

# 2. Update init() to load this data
init_marker = "function init() {"
if init_marker in content:
    # We want to replace the body of init()
    # It currently has:
    # const daysDisplay ...
    # if (daysDisplay) ...
    # itineraryData = [];
    # for (...) ...
    # renderItinerary();
    
    # We'll replace the whole function with a smarter one.
    
    new_init = """function init() {
        // Initialize days
        const daysDisplay = document.getElementById('daysDisplay');
        const numberOfDaysInput = document.getElementById('numberOfDaysInput');

        // Check for existing data
        const serverItineraryEl = document.getElementById('server-itinerary-data');
        const serverDestinationsEl = document.getElementById('server-destinations-data');

        if (serverItineraryEl) {
            try {
                itineraryData = JSON.parse(serverItineraryEl.textContent);
                // Ensure legacy fields if missing
                itineraryData.forEach((day, idx) => {
                   if (!day.items) day.items = []; 
                   // Fix indices
                   day.day = idx + 1;
                });
                
                TRIP_DAYS = itineraryData.length; // Update trip days based on saved data
                
                // If we have saved destinations, pre-select them
                if (serverDestinationsEl) {
                    try {
                        const savedDestinations = JSON.parse(serverDestinationsEl.textContent);
                        if (savedDestinations && Array.isArray(savedDestinations)) {
                            selectedDestinations = savedDestinations;
                            
                            // Mark them visually
                            setTimeout(() => {
                                selectedDestinations.forEach(d => {
                                    const el = document.querySelector(`.destination-card[data-id="${d.id}"]`);
                                    if (el) {
                                        el.classList.add('selected-destination');
                                        const checkbox = el.querySelector('.destination-checkbox');
                                        if (checkbox) checkbox.classList.remove('hidden');
                                    }
                                });
                                
                                // Update TRIP_DESTINATIONS
                                TRIP_DESTINATIONS = selectedDestinations.map(d => {
                                    return ALL_DESTINATIONS.find(ad => ad.id === d.id);
                                }).filter(d => d);
                                
                                // Update input
                                const destinationIdsInput = document.getElementById('destinationIdsInput');
                                if (destinationIdsInput) {
                                    destinationIdsInput.value = selectedDestinations.map(d => d.id).join(',');
                                }
                                
                                // Re-render to ensure name linking
                                renderItinerary();
                            }, 500); // Delay slightly to ensure DOM is ready
                        }
                    } catch (e) { console.error("Error parsing saved destinations", e); }
                }

            } catch (e) {
                console.error("Error parsing server itinerary", e);
                // Fallback to new trip
                generateNewItinerary();
            }
        } else {
            // New trip
            generateNewItinerary();
        }

        if (daysDisplay) daysDisplay.innerText = TRIP_DAYS;
        if (numberOfDaysInput) numberOfDaysInput.value = TRIP_DAYS;

        renderItinerary();
    }

    function generateNewItinerary() {
        itineraryData = [];
        for (let i = 1; i <= TRIP_DAYS; i++) {
            itineraryData.push({
                day: i,
                start_location: '',
                start_time: '09:00',
                items: [],
                end_location: ''
            });
        }
    }"""
    
    # We need to find where init() ends. It ends at `}` before `// --- RENDER LOGIC ---` (which I added in previous script) 
    # or `renderItinerary();\n    }`
    
    # Actually, I can just Regex replace the function init() { ... } block.
    # The current init function body is predictable.
    import re
    # Match function init() { ... renderItinerary(); }
    # Be careful with nested braces. Regex is bad for nested braces.
    # But init() is simple.
    
    # Let's find start and end indices using brace counting or just replace known content.
    # Current init:
    # function init() {
    #     // Initialize days
    #     ...
    #     renderItinerary();
    # }
    
    start_idx = content.find(init_marker)
    if start_idx != -1:
        # Scan for matching brace
        brace_count = 0
        end_idx = -1
        for i in range(start_idx, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        if end_idx != -1:
            content = content[:start_idx] + new_init + content[end_idx:]
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Successfully patched init() and inserted data scripts.")
        else:
            print("Could not find end of init function.")
    else:
        print("Could not find init function.")

else:
    print("Could not find marker for input.")

