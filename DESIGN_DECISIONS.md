# Design Decisions and Ambiguity Resolutions

This document clarifies ambiguities in the requirements and documents implementation decisions.

## 1. Minimum Places Requirement

**Requirement (Line 11):** "One project can contain multiple places (minimum: 1, maximum: 10)"

**Ambiguity:** Can a project be created with 0 places initially?

**Decision:** ✅ **YES - Projects can be created empty**
- **Rationale:** 
  - Two separate requirements exist: "create a project" (lines 16-17) and "create a project with places" (line 24)
  - Real-world use case: Create project first, add places later as you discover them
  - Flexibility for users planning trips incrementally
- **Implementation:**
  - `POST /projects` - creates empty project
  - `POST /projects` with `places` array - creates project with places
  - `POST /projects/{id}/places` - adds places to existing project

---

## 2. Art Institute API - What are "Places"?

**Requirement (Lines 40-43):** Use Art Institute of Chicago API for places

**Ambiguity:** The Art Institute API is for artworks, not geographic locations. What are "places"?

**Decision:** ✅ **Artworks are "places" to visit in the museum**
- **Interpretation:** A travel project is a museum visit itinerary
- **Example:**
  - Project: "Summer Chicago Trip"
  - Places: "A Sunday on La Grande Jatte", "Nighthawks", "American Gothic"
  - User marks each artwork as "visited" when they see it
- **Rationale:**
  - Requirement explicitly states to use Art Institute API
  - Makes sense as a cultural tourism app
  - "Places to visit" = "artworks to see"

---

## 3. Place Uniqueness - External ID vs Name

**Requirement (Lines 26, 48):** 
- "Each place is identified by an external ID from the API"
- "Prevent adding the same external place to the same project more than once"

**Ambiguity:** What identifies uniqueness - `external_id` or `place_name`?

**Decision:** ✅ **Check uniqueness by `place_name` (case-insensitive)**
- **Rationale:**
  - User inputs `place_name`, API lookup populates `external_id`
  - Two places with same name would confuse users
  - Prevents accidental duplicates from typos/variations
- **Implementation:**
  ```python
  if any(p.place_name.lower() == place.place_name.lower() for p in self.places):
      raise ValueError(f"Place with name '{place.place_name}' already exists")
  ```

**Alternative considered:** Check by `external_id` after API lookup
- Rejected: Would allow duplicate names if they somehow mapped to different IDs

---

## 4. User Management

**Ambiguity:** No requirements for user creation/authentication

**Decision:** ✅ **Users exist but have minimal CRUD endpoints**
- **Implementation:**
  - `POST /users` - create user (simple name only)
  - `GET /users/{id}` - get user by ID
  - `GET /users` - list all users
- **Not Implemented:**
  - Authentication/authorization (bonus points mention "basic authentication")
  - Login/logout
  - User sessions
- **Rationale:** Focus on core travel project requirements within 2-hour timeframe

---

## 5. Project Completion Behavior

**Requirement (Line 11):** "When all places in a project are marked as visited, the project is marked as completed."

**Ambiguity:** Can completion be reversed? Can places be added to completed projects?

**Decision:** ✅ **Completion is bidirectional and dynamic**
- **Behaviors:**
  - Marking all places visited → `completed = true` (automatic)
  - Unmarking any place → `completed = false` (automatic)
  - Adding a new place to completed project → `completed = false`
  - Completed projects can still be modified
- **Implementation:** Automatic via `place.update_visited()` back-reference
- **Rationale:**
  - Real-world: Users make mistakes, need to undo
  - Real-world: Users discover new places mid-trip
  - Flexibility over rigid state machine

---

## 6. Updateable Place Fields

**Requirement (Lines 29-31):** Update `notes` and `visited` status

**Ambiguity:** Can other fields (`place_name`, `external_id`, `api_link`) be updated?

**Decision:** ✅ **Only `notes` and `visited` are updateable**
- **Immutable fields:**
  - `place_name` - tied to API lookup
  - `external_id` - identity from API
  - `api_link` - reference to API resource
- **Rationale:**
  - These fields come from third-party API (shouldn't be edited)
  - Changing them would break data integrity
  - To "change" a place, delete and re-add it

---

## 7. Empty Project Deletion

**Requirement (Line 19):** "A project cannot be deleted if any of its places are already marked as visited"

**Ambiguity:** Can projects with 0 places be deleted?

**Decision:** ✅ **YES - Empty projects can be deleted**
- **Logic:** `can_delete() = not any(place.visited for place in self.places)`
  - 0 places → empty list → `any()` returns `False` → `not False` = `True`
- **Rationale:**
  - Natural interpretation: "no visited places" includes "no places at all"
  - Users should be able to delete projects they haven't started

---

## 8. API Caching Strategy

**Bonus Point (Line 60):** "Caching responses from the third-party API"

**Decision:** ✅ **Implemented in-memory cache with TTL**
- **Strategy:**
  - Cache keyed by search query
  - Default TTL: 1 hour (configurable)
  - Cache stored in `APICache` class
- **Not implemented:** Redis/persistent cache (overkill for 2-hour assessment)

---

## 9. Project Creation with Places - Atomicity

**Requirement (Line 24):** "Ability to create a project with places in one single request"

**Decision:** ✅ **All-or-nothing validation**
- **Behavior:**
  - Validate ALL places against API before creating project
  - If ANY place fails validation → entire operation fails
  - No partial project creation
- **Implementation:** `Project.create_with_places()` validates all before committing
- **Rationale:**
  - Transactional integrity
  - Better UX: User knows immediately if any place is invalid

---

## Summary

These decisions prioritize:
1. **Flexibility** - Users can work incrementally
2. **Data integrity** - External API data is immutable
3. **User experience** - Mistakes can be undone, clear error messages
4. **Simplicity** - 2-hour scope, avoid over-engineering

All decisions align with the spirit of the requirements while resolving ambiguities pragmatically.
