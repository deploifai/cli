//go:generate go run github.com/Khan/genqlient
package api

import (
	"context"
	"fmt"
	"github.com/Khan/genqlient/graphql"
	"net/http"
	"os"
)

type APIClient struct {
	ClientObject  graphql.Client
	ClientCreated bool
}

func CreateClient() APIClient {
	var backendURL string = os.Getenv("backend_url")
	httpClient := http.Client{}
	apiClient := APIClient{}
	apiClient.ClientObject = graphql.NewClient(fmt.Sprintf("%s/graphql", backendURL), &httpClient)
	apiClient.ClientCreated = true
	return apiClient
}

func (apiClient *APIClient) GetUser() *GetUserResponse {
	if apiClient.ClientCreated {
		user, err := GetUser(context.Background(), apiClient.ClientObject)
		if err != nil {
			return nil
		}
		return user
	}
	return nil
}
