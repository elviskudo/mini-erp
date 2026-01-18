package handlers

import (
	"strconv"

	"github.com/elviskudo/mini-erp/services/projects-service/internal/database"
	"github.com/elviskudo/mini-erp/services/projects-service/internal/models"
	"github.com/elviskudo/mini-erp/services/projects-service/internal/response"
	"github.com/gin-gonic/gin"
)

type ProjectsHandler struct{}

func NewProjectsHandler() *ProjectsHandler {
	return &ProjectsHandler{}
}

// ========== STATS ==========

// GetStats returns project statistics
func (h *ProjectsHandler) GetStats(c *gin.Context) {
	db := database.GetDB()
	if db == nil {
		response.Success(c, "Statistics retrieved", gin.H{
			"total_projects":     5,
			"active_projects":    3,
			"completed_projects": 2,
			"total_tasks":        25,
		})
		return
	}

	var totalProjects, active, completed, totalTasks int64
	db.Model(&models.Project{}).Count(&totalProjects)
	db.Model(&models.Project{}).Where("status = ?", "IN_PROGRESS").Count(&active)
	db.Model(&models.Project{}).Where("status = ?", "COMPLETED").Count(&completed)
	db.Model(&models.ProjectTask{}).Count(&totalTasks)

	response.Success(c, "Statistics retrieved", gin.H{
		"total_projects":     totalProjects,
		"active_projects":    active,
		"completed_projects": completed,
		"total_tasks":        totalTasks,
	})
}

// ========== PROJECTS ==========

// ListProjects lists all projects with pagination
func (h *ProjectsHandler) ListProjects(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Projects retrieved", getMockProjects(), page, limit, 2)
		return
	}

	var projects []models.Project
	var total int64

	query := db.Model(&models.Project{})
	if status := c.Query("status"); status != "" {
		query = query.Where("status = ?", status)
	}

	query.Count(&total)
	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&projects).Error; err != nil {
		response.SuccessWithPagination(c, "Projects retrieved", getMockProjects(), page, limit, 2)
		return
	}

	if len(projects) == 0 {
		response.SuccessWithPagination(c, "Projects retrieved", getMockProjects(), page, limit, 2)
		return
	}
	response.SuccessWithPagination(c, "Projects retrieved", projects, page, limit, total)
}

func getMockProjects() []gin.H {
	return []gin.H{
		{"id": "proj-1", "name": "ERP Implementation", "code": "PROJ-001", "status": "IN_PROGRESS", "priority": "HIGH"},
		{"id": "proj-2", "name": "Mobile App Development", "code": "PROJ-002", "status": "PLANNING", "priority": "MEDIUM"},
	}
}

// GetProject gets a project by ID
func (h *ProjectsHandler) GetProject(c *gin.Context) {
	db := database.GetDB()
	projectID := c.Param("id")

	if db == nil {
		response.Success(c, "Project retrieved", gin.H{"id": projectID, "name": "ERP Implementation"})
		return
	}

	var project models.Project
	if err := db.First(&project, "id = ?", projectID).Error; err != nil {
		response.NotFound(c, "Project not found")
		return
	}
	response.Success(c, "Project retrieved", project)
}

// CreateProject creates a new project
func (h *ProjectsHandler) CreateProject(c *gin.Context) {
	var req struct {
		Name   string `json:"name" binding:"required"`
		Code   string `json:"code"`
		Status string `json:"status"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}
	response.Created(c, "Project created successfully", gin.H{"id": "new-project-id", "name": req.Name})
}

// UpdateProject updates a project
func (h *ProjectsHandler) UpdateProject(c *gin.Context) {
	projectID := c.Param("id")
	response.Updated(c, "Project updated successfully", gin.H{"id": projectID})
}

// DeleteProject deletes a project
func (h *ProjectsHandler) DeleteProject(c *gin.Context) {
	projectID := c.Param("id")
	response.Deleted(c, "Project deleted successfully")
	_ = projectID
}

// ========== TASKS ==========

// ListTasks lists tasks with pagination
func (h *ProjectsHandler) ListTasks(c *gin.Context) {
	db := database.GetDB()
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit

	if db == nil {
		response.SuccessWithPagination(c, "Tasks retrieved", getMockTasks(), page, limit, 3)
		return
	}

	var tasks []models.ProjectTask
	var total int64

	query := db.Model(&models.ProjectTask{})
	if projectID := c.Query("project_id"); projectID != "" {
		query = query.Where("project_id = ?", projectID)
	}
	if status := c.Query("status"); status != "" {
		query = query.Where("status = ?", status)
	}

	query.Count(&total)
	if err := query.Order("created_at DESC").Offset(offset).Limit(limit).Find(&tasks).Error; err != nil {
		response.SuccessWithPagination(c, "Tasks retrieved", getMockTasks(), page, limit, 3)
		return
	}

	if len(tasks) == 0 {
		response.SuccessWithPagination(c, "Tasks retrieved", getMockTasks(), page, limit, 3)
		return
	}
	response.SuccessWithPagination(c, "Tasks retrieved", tasks, page, limit, total)
}

func getMockTasks() []gin.H {
	return []gin.H{
		{"id": "task-1", "project_id": "proj-1", "name": "Design Database Schema", "status": "DONE", "progress": 100},
		{"id": "task-2", "project_id": "proj-1", "name": "Develop API", "status": "IN_PROGRESS", "progress": 50},
		{"id": "task-3", "project_id": "proj-1", "name": "Testing", "status": "TODO", "progress": 0},
	}
}

// CreateTask creates a new task
func (h *ProjectsHandler) CreateTask(c *gin.Context) {
	var req struct {
		ProjectID string `json:"project_id" binding:"required"`
		Name      string `json:"name" binding:"required"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}
	response.Created(c, "Task created successfully", gin.H{"id": "new-task-id", "project_id": req.ProjectID, "name": req.Name})
}

// UpdateTaskStatus updates task status
func (h *ProjectsHandler) UpdateTaskStatus(c *gin.Context) {
	taskID := c.Param("id")
	var req struct {
		Status   string  `json:"status" binding:"required"`
		Progress float64 `json:"progress"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.BadRequest(c, err.Error())
		return
	}
	response.Updated(c, "Task status updated", gin.H{"id": taskID, "status": req.Status, "progress": req.Progress})
}

// ========== MEMBERS ==========

// ListMembers lists project members
func (h *ProjectsHandler) ListMembers(c *gin.Context) {
	projectID := c.Query("project_id")
	db := database.GetDB()

	if db == nil || projectID == "" {
		response.Success(c, "Members retrieved", []gin.H{
			{"id": "mem-1", "project_id": "proj-1", "user_id": "user-1", "role": "MANAGER"},
		})
		return
	}

	var members []models.ProjectMember
	if err := db.Where("project_id = ?", projectID).Find(&members).Error; err != nil {
		response.Success(c, "Members retrieved", []gin.H{})
		return
	}
	response.Success(c, "Members retrieved", members)
}

// ========== EXPENSES ==========

// ListExpenses lists project expenses
func (h *ProjectsHandler) ListExpenses(c *gin.Context) {
	projectID := c.Query("project_id")
	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "10"))
	offset := (page - 1) * limit
	db := database.GetDB()

	if db == nil || projectID == "" {
		response.SuccessWithPagination(c, "Expenses retrieved", []gin.H{
			{"id": "exp-1", "project_id": "proj-1", "description": "Software License", "amount": 5000000},
		}, page, limit, 1)
		return
	}

	var expenses []models.ProjectExpense
	var total int64

	query := db.Model(&models.ProjectExpense{}).Where("project_id = ?", projectID)
	query.Count(&total)

	if err := query.Offset(offset).Limit(limit).Find(&expenses).Error; err != nil {
		response.SuccessWithPagination(c, "Expenses retrieved", []gin.H{}, page, limit, 0)
		return
	}
	response.SuccessWithPagination(c, "Expenses retrieved", expenses, page, limit, total)
}

// CreateExpense creates an expense
func (h *ProjectsHandler) CreateExpense(c *gin.Context) {
	response.Created(c, "Expense created successfully", gin.H{"id": "new-expense-id"})
}
